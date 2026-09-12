# Hospedar o Arbites num servidor próprio

Guia para tirar o Arbites do `localhost` e colocá-lo num servidor de casa
(UmbrelOS ou qualquer host com Docker), acessível pela internet por um
Cloudflare Tunnel.

Leia a seção **Backup** antes de convidar alguém: o `auth.db` é o único dado
da instalação que não se reconstrói.

---

## 1. Arquitetura

```
Internet → Cloudflare → cloudflared → http://arbites:8347
                        (container)   └─ FastAPI serve a API e a SPA
                                         na MESMA origem
```

Um container só. O FastAPI serve o build do React como estático, então a
sessão vive num cookie `httpOnly` + `SameSite=Lax` — sem CORS, sem token no
`localStorage`, sem nada legível a JavaScript.

A porta 8347 **não** é publicada no host. A única entrada é o hostname do
túnel; um `ports:` no compose abriria um caminho paralelo, sem o Cloudflare
na frente.

### Por que não passar pelo proxy do BFFless

Se você já roda o [BFFless](https://bffless.dev) no mesmo servidor, a
tentação é registrar o Arbites como uma *proxy rule* dele e herdar a
autenticação do SuperTokens. Não funciona, por quatro motivos concretos:

1. **O proxy não diz ao backend quem é o usuário.** Ele remove os headers
   `cookie` e `authorization` por padrão e não documenta injeção de
   identidade. O Arbites receberia tudo como anônimo — e a autoria das
   execuções, que é a razão de existir da rastreabilidade, morreria.
2. **Não há log de auditoria documentado.** As abas Acessos e Atividade
   teriam de ser construídas aqui de qualquer forma.
3. **O SSE quebra.** O timeout do proxy é de 60s no máximo e streaming não é
   documentado; `GET /runs/{exec_id}/stream` transmite o log do Behave ao
   vivo e qualquer regressão de mais de um minuto seria cortada.
4. **O alvo do proxy precisa ser HTTPS público.** A documentação bloqueia
   `localhost` e faixas privadas, e recusa `http://` para host não-interno —
   que é exatamente a forma de `http://arbites:8347`.

O `cloudflared` não tem nenhuma dessas restrições: rotear para HTTP interno
é literalmente a função dele. Os dois convivem no mesmo servidor, cada um
com seu hostname, sem acoplamento.

---

## 2. Subir

### 2.1. Configuração

Crie um `.env` ao lado do `docker-compose.yml`:

```dotenv
ARBITES_ADMIN_EMAIL=voce@seudominio.com
ARBITES_ADMIN_PASSWORD=uma-senha-longa-de-instalacao
ARBITES_SIGNUP=on
TUNNEL_TOKEN=<token do túnel, passo 2.2>
```

A senha de admin vem do ambiente, então ela é visível em `docker inspect` e
no histórico do shell. Por isso a conta nasce com **troca obrigatória**: ela
serve para o primeiro login e nada mais. Depois de entrar e trocar, pode
remover as duas variáveis — o bootstrap só roda quando não existe nenhum
admin ativo.

### 2.2. Túnel na Cloudflare

No painel Zero Trust → **Networks → Tunnels → Create a tunnel**:

1. Escolha *Cloudflared*, dê um nome, copie o **token** para o `.env`.
2. Em **Public Hostnames**, adicione:
   - Subdomain: `arbites` · Domain: o seu
   - Service: **HTTP** → `arbites:8347`

`arbites` é o nome do serviço no compose; os dois containers estão na mesma
rede Docker, então o DNS interno resolve.

### 2.3. Subir

```bash
docker compose up -d --build
docker compose logs -f arbites   # deve dizer que criou o admin de bootstrap
```

Abra `https://arbites.seudominio.com`, entre com as credenciais do `.env`,
troque a senha.

---

## 3. Primeiros passos como admin

Em **Administração** (a aba só aparece para o papel `admin`):

1. **Sistema** → desligue o que esta instância não usa. Cada interruptor
   fecha uma superfície que, exposta, tem custo real:

   | Interruptor | O que fecha | Desligue se |
   |---|---|---|
   | `local_runner` | execução de Behave em subprocess no servidor | você não roda automação por aqui |
   | `filesystem_browse` | navegação do filesystem do servidor | não usa a busca de `.feature` pela UI |
   | `target_env` | leitura e escrita do `.env` dos projetos-alvo | os alvos guardam credenciais |
   | `ai` | chamadas aos providers de IA | não usa IA, ou não quer que saia tráfego |
   | `xray_import` | importação de XML do Xray | a migração já acabou |

   Vale na hora, sem reiniciar.

2. **Usuários** → à medida que as pessoas se cadastram, elas aparecem em
   *Aguardando liberação*. Escolha o papel na própria liberação:

   - `viewer` — só lê. Nenhuma escrita, em nenhuma rota.
   - `editor` — o QA do dia a dia: requisitos, casos, execuções, defeitos,
     e disparar execuções de alvos já configurados.
   - `admin` — o acima, mais as superfícies governadas e este painel.

3. Quando o time inteiro estiver dentro, mude `ARBITES_SIGNUP=off` e
   reinicie. A partir daí as contas nascem só por aqui.

### O que é privilégio de admin, e por quê

`PUT /targets` é a rota mais perigosa da aplicação — não `POST /runs/local`,
como parece. Um *target* define `python_path` e `working_dir` de um
subprocess: quem escreve um alvo escolhe qual binário o servidor executa.
Rodar um alvo já configurado é trabalho de QA; configurá-lo é administração.

---

## 4. Backup

O volume `arbites-data` guarda duas coisas de naturezas diferentes:

- `/data/workspace` — a fonte de verdade em Markdown/YAML/JSON. Versionável
  em git, legível no Obsidian, reconstruível a partir de qualquer cópia.
- `/data/workspace/.arbites/auth.db` — **contas, sessões e o log de
  atividade.** Não está em git (o `.arbites/` é ignorado por construção,
  ADR 0011) e não se reconstrói a partir de nada. Perder este arquivo é
  perder todas as contas e toda a trilha de auditoria.

O `index.db` no mesmo diretório é descartável: apague e reindexe à vontade.

```bash
# cópia consistente do volume inteiro
docker run --rm -v arbites-data:/data -v "$PWD:/backup" alpine \
  tar czf /backup/arbites-$(date +%F).tar.gz -C /data .
```

Guarde fora do servidor. Um backup que mora no mesmo disco não é backup.

---

## 5. Operação

```bash
docker compose logs -f arbites        # log da aplicação
docker compose restart arbites        # reiniciar
docker compose up -d --build          # atualizar depois de um git pull
```

**IP real.** Atrás do túnel, o endereço do socket é sempre o do proxy. O
Arbites lê `CF-Connecting-IP` (e cai para `X-Forwarded-For`), então o IP que
aparece nas abas Acessos e Atividade é o do visitante de verdade.

**Perdi o acesso de admin.** Pare o container, defina
`ARBITES_ADMIN_EMAIL`/`ARBITES_ADMIN_PASSWORD` com um e-mail que ainda não
existe e suba: sem nenhum admin ativo o bootstrap roda de novo. Se ainda
houver um admin ativo, ele não roda — nesse caso o caminho é outro admin
redefinir a senha pelo painel.

**Rodar sem autenticação.** `ARBITES_AUTH=off` desliga o gate inteiro e a
aplicação volta ao comportamento de instalação local. Só faz sentido numa
rede confiável, nunca atrás de um túnel público: sem o gate, `PUT /targets`
está aberto a qualquer visitante, o que é execução de código no seu
servidor. O log de inicialização avisa em letras garrafais.

---

## 6. Rodar sem túnel (rede local)

Publique a porta e acesse pelo IP da máquina:

```yaml
    ports: ["8347:8347"]
```

O cookie de sessão só recebe a flag `Secure` em HTTPS; em HTTP na rede local
ele funciona, mas trafega em claro. Para uso só-LAN é aceitável; para
qualquer coisa que atravesse a internet, use o túnel.
