# Hospedar o Arbites num servidor próprio

Guia para tirar o Arbites do `localhost` e colocá-lo num servidor de casa,
acessível pela internet por um Cloudflare Tunnel. Escrito para UmbrelOS
convivendo com o BFFless, mas serve para qualquer host com Docker.

Leia a seção **Backup** antes de convidar alguém: o `auth.db` é o único dado
da instalação que não se reconstrói.

---

## 1. Arquitetura

O Arbites reaproveita o **Cloudflare Tunnel que já roda no Umbrel** — o
mesmo app da loja que expõe o BFFless. Um túnel só, um lugar só para olhar
quando algo não responde.

```
                            ┌─ arbites.seu.com  → umbrel.local:8347 → Arbites
Internet → Cloudflare → cloudflared ─┤
            (app do Umbrel)          └─ *.seu.com       → umbrel.local:5537 → BFFless
```

Um container para o Arbites. O FastAPI serve o build do React como estático,
então a sessão vive num cookie `httpOnly` + `SameSite=Lax` — sem CORS, sem
token no `localStorage`, sem nada legível a JavaScript.

A porta 8347 é publicada no host: é assim que o `cloudflared` do Umbrel
chega até ela, do mesmo jeito que chega no `5537` do BFFless. Isso também
deixa o Arbites visível na LAN, e tudo bem — **o gate de sessão vale para
qualquer entrada**. Quem chega pela rede local encontra a mesma tela de
login que quem chega pela internet; é um caminho a mais para o mesmo
porteiro, não um desvio dele.

> **`umbrel.local` é só o padrão.** O hostname é o do seu dispositivo e pode
> ser outro (`rp4.local`, por exemplo). Confirme com `hostname` no SSH e use
> o seu em todo lugar onde este guia escreve `umbrel.local`.

> Se você prefere que o Arbites seja inalcançável sem passar pela
> Cloudflare, veja a seção **2.4** (mesmo túnel, sem porta publicada) ou a
> **2.6** (túnel dedicado, com um segundo token).

### O wildcard do BFFless captura tudo — e como conviver com ele

A [instalação do BFFless no Umbrel](https://docs.bffless.dev/deployment/umbrel/)
registra dois routes apontando para `umbrel.local:5537`: o apex
`seudominio.com` e o **wildcard `*.seudominio.com`**, mais um CNAME `*` no
DNS. A própria documentação avisa que o domínio não serve para mais nada
depois disso — o wildcard engole todos os subdomínios.

Sem cuidado, `arbites.seudominio.com` cairia no BFFless.

O desempate é a ordem dos routes: no painel Zero Trust os *Public Hostnames*
são avaliados de cima para baixo, primeiro match vence. Basta o específico
ficar **acima** do wildcard (a lista é reordenável arrastando). O passo a
passo está em 2.2.

Note que isto é sobre o **túnel** ser compartilhado, não o proxy: o
`cloudflared` roteia por hostname sem tocar em nada da requisição. O proxy
do BFFless continua fora do caminho, pelos motivos abaixo.

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
   que é exatamente a forma de `http://umbrel.local:8347`.

O `cloudflared` não tem nenhuma dessas restrições: rotear para HTTP interno
é literalmente a função dele. Os dois convivem no mesmo servidor, cada um
com seu hostname, sem acoplamento.

---

## 2. Subir

Pressuposto: o app **Cloudflare Tunnel** do Umbrel já está instalado e
funcionando (foi ele que você configurou ao subir o BFFless). Se ainda não
estiver, siga os passos 2 a 4 da
[instalação do BFFless](https://docs.bffless.dev/deployment/umbrel/) — a
parte do túnel é a mesma.

### 2.1. Configuração

Por SSH no Umbrel, clone o repositório e crie um `.env` ao lado do
`docker-compose.yml`:

```dotenv
ARBITES_ADMIN_EMAIL=voce@seudominio.com
ARBITES_ADMIN_PASSWORD=uma-senha-longa-de-instalacao
ARBITES_SIGNUP=on
```

Não há `TUNNEL_TOKEN` aqui: quem tem o token é o app do Umbrel.

A senha de admin vem do ambiente, então ela é visível em `docker inspect` e
no histórico do shell. Por isso a conta nasce com **troca obrigatória**: ela
serve para o primeiro login e nada mais. Depois de entrar e trocar, pode
remover as duas variáveis — o bootstrap só roda quando não existe nenhum
admin ativo.

### 2.2. Subir o container

```bash
docker compose up -d --build
docker compose logs -f arbites   # deve dizer que criou o admin de bootstrap
```

Confirme pela LAN antes de mexer na Cloudflare — separa um problema de
container de um problema de rede:

```bash
curl http://umbrel.local:8347/api/v1/health
# {"status":"ok","version":"..."}
```

`/api/v1/health` é a única rota da API que responde sem sessão; qualquer
outra devolvendo `401` é sinal de que o gate está de pé, não de erro.

### 2.3. Route no túnel — a ordem importa

> **Sem domínio?** Esta seção precisa de um domínio na sua conta Cloudflare
> (é o que dá nome ao hostname). Se você não tem um, pule para a **§2.5**:
> o túnel funciona no modo de rede privada, sem domínio nenhum.

No painel Zero Trust → **Networks → Tunnels** → seu túnel → **Public
Hostnames**:

1. **Add a public hostname**
   - Subdomain: `arbites` · Domain: o seu
   - Service: **HTTP** → `umbrel.local:8347`
2. **Arraste-o para o topo da lista**, acima do `*.seudominio.com` do
   BFFless.

A lista é avaliada de cima para baixo e o primeiro match vence. Se o
wildcard ficar em cima, `arbites.seudominio.com` vai parar no BFFless e você
verá a tela dele — é o sintoma exato desse erro de ordenação.

Resultado esperado:

| Ordem | Hostname | Serviço |
|---|---|---|
| 1 | `arbites.seudominio.com` | `HTTP umbrel.local:8347` |
| 2 | `*.seudominio.com` | `HTTP umbrel.local:5537` |
| 3 | `seudominio.com` | `HTTP umbrel.local:5537` |

DNS: nada a fazer. O CNAME `*` que a instalação do BFFless criou já resolve
`arbites.seudominio.com` para o mesmo túnel.

Abra `https://arbites.seudominio.com`, entre com as credenciais do `.env`,
troque a senha.

### 2.4. Variante: sem publicar a porta, na rede do túnel

O `cloudflared` do Umbrel alcança outros containers pelo **nome**, não só
por `<host>:<porta>` — é como a
[wiki do app](https://github.com/Radiokot/umbrel-cloudflared/wiki/How-to-set-up-Cloudflare-Tunnel-on-your-Umbrel)
roteia apps protegidos (`http://photoprism_web_1:8087`). Dá para usar isso e
ficar sem porta publicada, mantendo o túnel compartilhado.

Descubra a rede do container do túnel:

```bash
# nome do container do túnel
docker ps --format '{{.Names}}' | grep -i cloudflared

# as redes dele — os nomes são as chaves do JSON
docker inspect -f '{{json .NetworkSettings.Networks}}' <container>
```

No `docker-compose.yml`, troque `ports` por `expose`, fixe o nome do
container e entre naquela rede:

```yaml
  arbites:
    container_name: arbites
    expose: ["8347"]
    networks: [tunel]

networks:
  tunel:
    external: true
    name: <a rede que o comando acima mostrou>
```

O route no painel passa a apontar para `http://arbites:8347`.

Atenção: esta variante **não** combina com a rota privada da §2.5. Sem
porta publicada no host, não há IP:porta na sua rede para a rota privada
alcançar — só o nome do container, que o WARP não resolve.

Fica melhor que o caminho padrão — mesmo túnel, sem exposição na LAN — ao
custo de depender de um nome de rede interno do Umbrel, que pode mudar entre
versões. Por isso o padrão do repositório continua sendo a porta publicada:
funciona sem saber nada sobre a topologia interna do Umbrel. Se esta variante
parar de funcionar depois de uma atualização, o sintoma é 502 no hostname, e
voltar para `ports` resolve.

### 2.5. Sem domínio: rota privada + WARP

Route com hostname exige um domínio na sua conta Cloudflare. Se você ainda
não tem um — ou não quer ter —, o túnel funciona no outro modo: em vez de
publicar um endereço, ele **estende a sua rede local**. De qualquer lugar,
`http://<ip-do-umbrel>:8347` responde como se você estivesse em casa.

Descubra o IP do Umbrel na LAN:

```bash
hostname -I | awk '{print $1}'    # ex.: 192.168.1.42
```

No painel do túnel → **Add route** → **Private network**, informe
`192.168.1.42/32` (só o Umbrel) ou a faixa inteira da sua rede.

Depois, em **Zero Trust → Settings → WARP Client**:

1. **Device enrollment** — crie uma regra de quem pode entrar (o mais
   simples é *Emails* com os endereços do time).
2. **Split Tunnels** — este é o passo que faz todo mundo tropeçar. O WARP
   vem configurado para **excluir** faixas privadas (`192.168.0.0/16`,
   `10.0.0.0/8`), ou seja, ele ignora exatamente o endereço que você quer
   alcançar. Remova a faixa do seu Umbrel da lista de exclusão.

Instale o **Cloudflare One Client (WARP)** em cada dispositivo, faça login
com o nome da sua organização, e abra `http://192.168.1.42:8347`.

Duas consequências para decidir com consciência:

- **Cada pessoa precisa do WARP instalado e logado.** Não dá para mandar um
  link e a pessoa abrir no navegador; isso só com domínio.
- **O tráfego é HTTP dentro do túnel.** Não há TLS ponta a ponta como no
  modo com hostname, então o cookie de sessão não recebe a flag `Secure`.
  A conexão até a borda da Cloudflare é criptografada pelo WARP; o trecho
  final, não. Aceitável para um time pequeno; para acesso amplo, use
  hostname com domínio.

> **Não use *quick tunnel* (`trycloudflare.com`) para esta aplicação.** É o
> outro modo sem domínio, mas a documentação da Cloudflare lista "no
> Server-Sent Events support" entre as limitações — e o log ao vivo da
> automação é SSE. Some a isso a URL que muda a cada reinício e a ausência
> de SLA.

### 2.6. Alternativa: túnel dedicado

Se você quiser que o Arbites seja inalcançável sem passar pela Cloudflare —
nem pela LAN —, crie um segundo túnel e deixe o `cloudflared` junto do
Arbites. O rodapé do `docker-compose.yml` traz o bloco pronto: troque
`ports` por `expose`, ponha os dois serviços numa rede comum, e cole o
`TUNNEL_TOKEN` do túnel novo no `.env`.

Aí o desempate contra o wildcard do BFFless acontece no **DNS**, não na
ordem dos routes: ao criar o Public Hostname no túnel novo, a Cloudflare
grava um CNAME explícito `arbites` → `<tunnel>.cfargotunnel.com`, e registro
exato sempre vence wildcard. O BFFless nunca vê a requisição.

O custo é administrar dois túneis e dois tokens, e o Arbites fica fora da UI
do Umbrel (sobe sozinho pelo `restart: unless-stopped`, mas não aparece na
lista de apps).

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

**Log de automação ao vivo.** O Cloudflare Tunnel passa HTTP e WebSocket; o
stream do run é SSE, que é HTTP comum e atravessa sem problema. O que
atrapalharia é a borda derrubar conexão ociosa (~100s) durante um passo
silencioso do Behave — por isso o servidor emite um comentário de keepalive
a cada 15s. Se o terminal ainda assim congelar, é sinal de outra coisa: veja
`docker compose logs -f arbites`.

**IP real.** Atrás do túnel, o endereço do socket é sempre o do proxy. O
Arbites lê `CF-Connecting-IP` (e cai para `X-Forwarded-For`), então o IP que
aparece nas abas Acessos e Atividade é o do visitante de verdade.

**Abri `arbites.seudominio.com` e apareceu o BFFless.** O wildcard dele
está acima do route do Arbites na lista de Public Hostnames. Arraste o
específico para o topo; vale em segundos, sem reiniciar nada.

**Erro 502 no hostname do Arbites.** O túnel chegou e o container não
respondeu. Confira nesta ordem: `docker compose ps` (está de pé?),
`curl http://umbrel.local:8347/api/v1/health` do próprio Umbrel (responde
localmente?) e só então o route (`umbrel.local:8347`, HTTP, não HTTPS).

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

## 6. Acesso pela rede local

A porta 8347 é publicada no host, então `http://umbrel.local:8347` funciona
de dentro da rede sem passar pela Cloudflare. É o caminho útil para testar a
subida e para trabalhar se a internet cair.

Duas consequências que valem estar claras:

- **O login vale igual.** O gate de sessão não sabe por onde a requisição
  entrou; quem chega pela LAN vê a mesma tela e obedece aos mesmos papéis.
- **O cookie trafega em claro.** A flag `Secure` só é aplicada em HTTPS. Na
  LAN isso é aceitável; pela internet, sempre o túnel — que termina TLS na
  borda da Cloudflare.

Para fechar a LAN por completo, use a seção 2.4 (entrar na rede do túnel
do Umbrel) ou a 2.6 (túnel dedicado). Em ambas o container deixa de ter
porta publicada e só é alcançável de dentro do Docker.
