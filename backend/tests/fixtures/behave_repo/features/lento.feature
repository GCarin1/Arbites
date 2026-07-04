# language: pt
Funcionalidade: Cenário lento

  @CT-9003
  Cenário: Espera longa
    Dado que o usuário está na tela de login
    Quando esperar muito tempo
    Então deve visualizar o dashboard
