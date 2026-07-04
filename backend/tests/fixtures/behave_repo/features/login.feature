# language: pt
Funcionalidade: Login

  @CT-9001 @smoke
  Cenário: Login com credenciais válidas
    Dado que o usuário está na tela de login
    Quando informar credenciais válidas
    Então deve visualizar o dashboard

  @CT-9002 @smoke
  Cenário: Login com senha inválida
    Dado que o usuário está na tela de login
    Quando informar senha inválida
    Então deve falhar propositalmente

  @CT-9099
  Cenário: Cenário órfão sem CT correspondente
    Dado que o usuário está na tela de login
    Então deve visualizar o dashboard
