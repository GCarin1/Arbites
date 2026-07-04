import time

from behave import given, then, when


@given("que o usuário está na tela de login")
def step_tela_login(context):
    pass


@when("informar credenciais válidas")
def step_credenciais_validas(context):
    pass


@when("informar senha inválida")
def step_senha_invalida(context):
    pass


@when("esperar muito tempo")
def step_esperar(context):
    time.sleep(30)


@then("deve visualizar o dashboard")
def step_dashboard(context):
    pass


@then("deve falhar propositalmente")
def step_falha(context):
    raise AssertionError("falha esperada para teste de evidência")
