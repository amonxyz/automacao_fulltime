from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
import re
import psycopg2

def verificar_chave_acesso(conexao, chave):
    try:
        cursor = conexao.cursor()

        # Consulta SQL para verificar se a chave de acesso existe na tabela ChavesDeAcesso
        consulta = "SELECT Chave FROM MeuEsquema.ChavesDeAcesso WHERE Chave = %s;"
        cursor.execute(consulta, (chave,))

        # Verifica se a chave foi encontrada
        if cursor.fetchone() is not None:
            return True
        else:
            return False

    except Exception as e:
        print(f"Erro ao verificar a chave de acesso: {str(e)}")
        return False

def finalizar_evento(driver):
    try:
        volta_pag = driver.find_element(By.XPATH, '//*[@id="tab_status_em_espera"]/a')
        volta_pag.click()

    except Exception as e:
        print(f"Erro ao finalizar o evento: {str(e)}")

def coletar_eventos(driver):
    try:
        # Esperar até que o preloader desapareça
        wait = WebDriverWait(driver, 20)
        wait.until(EC.invisibility_of_element_located((By.ID, 'preloader')))

        with ThreadPoolExecutor(max_workers=5) as executor:
            while True:
                # Role para baixo para verificar mais eventos (ajuste conforme necessário)
                driver.execute_script("window.scrollBy(0, 500)")
                time.sleep(1)

                # Localizar elementos de eventos
                eventos = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='ocorrencia-item ng-scope']")))

                for evento in eventos:
                    try:
                        evento.click()
                        time.sleep(2)
                        texto_evento = evento.text.lower()

                        if "" in texto_evento:  # Conclui os eventos registrando em um arquivo TXT

                            # Obter o nome do cliente
                            nome_cliente_element = driver.find_element(By.XPATH, "//*[@id='descricaoEmpresa']/div/div/div/strong[4]")
                            nome_cliente = nome_cliente_element.text.strip()

                            # Obter o texto do elemento correspondente ao XPath desejado
                            elemento_descricao = driver.find_element(By.XPATH, '//*[@id="descricaoEmpresa"]/div/div/div/label')
                            texto_descricao = elemento_descricao.text.strip()

                            # Ajustar o nome do arquivo usando expressões regulares
                            nome_arquivo = re.sub(r'[^\w\s.-]', '', nome_cliente)
                            nome_arquivo = nome_arquivo.replace(' ', '_').replace('/', '').replace('-', '') + ".txt"

                            # Verificar se já existe um arquivo de relatório para o cliente
                            if os.path.exists(nome_arquivo):
                                # Se o arquivo já existe, abra e adicione o texto do evento
                                with open(nome_arquivo, "a", encoding="utf-8") as arquivo:
                                    arquivo.write("\n" + texto_evento)
                            else:
                                # Se o arquivo não existe, crie o arquivo e adicione o texto do evento
                                with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
                                    arquivo.write(texto_evento)

                            # Adicione o texto da descrição ao arquivo precedido por "Endereço:"
                            with open(nome_arquivo, "a", encoding="utf-8") as arquivo:
                                arquivo.write("\nEndereço: " + texto_descricao)

                            preencher_campo_texto(driver, texto_evento)
                            clicar_botao_gerar_comentario(driver)
                            clicar_botoes_finalizacao(driver)
                            finalizar_evento(driver)

                        if "" in texto_evento:  # Conclui o evento sem registrar
                            preencher_campo_texto(driver, texto_evento)
                            clicar_botao_gerar_comentario(driver)
                            clicar_botoes_finalizacao(driver)
                            finalizar_evento(driver)

                    except Exception as e:
                        print(f"Erro ao clicar no evento: {str(e)}")

    except Exception as e:
        print(f"Erro ao coletar eventos: {str(e)}")

# Função para clicar no botão "Gerar Comentário"
def clicar_botao_gerar_comentario(driver):
    try:
        # Localize o botão "Gerar Comentário" usando a classe
        botao_gerar_comentario = driver.find_element(By.CLASS_NAME, "generate-comment-button")
        botao_gerar_comentario.click()
        print("Botão 'Gerar Comentário' clicado")

        # Aguarde um tempo após clicar no botão "Gerar Comentário" antes de continuar (ajuste conforme necessário)
        time.sleep(2.3)  # Ajuste o tempo conforme necessário

    except Exception as e:
        print(f"Erro ao clicar no botão 'Gerar Comentário': {str(e)}")

# Função para clicar nos botões de finalização
def clicar_botoes_finalizacao(driver):
    try:
        # Aguarde até que a segunda aba seja carregada
        time.sleep(2.3)

        # Localize o primeiro botão "Finalizar" e clique
        botao_finalizar = driver.find_element(By.XPATH, "//button[@ng-click='preparaFinalizacaoOcorrencia()']")
        botao_finalizar.click()
        time.sleep(1.8)

        # Localize o segundo botão "Finalizar" pelo ID e clique
        botao_finalizar_2 = driver.find_element(By.ID, "btnFinalizarMotivoAlarme")
        botao_finalizar_2.click()
        time.sleep(1)

    except Exception as e:
        print(f"Erro ao clicar nos botões de finalização: {str(e)}")

# Função para preencher o campo de texto com as informações do evento
def preencher_campo_texto(driver, texto_evento):
    try:
        # Substitua o seletor pelo seletor correto do campo de texto
        campo_texto = driver.find_element(By.XPATH, "//textarea[@ng-model='occurrenceCommentVM.textField']")
        campo_texto.send_keys(texto_evento)

        # Capturar o nome do cliente do XPath
        nome_cliente = driver.find_element(By.XPATH, "//*[@id='descricaoEmpresa']/div/div/div/strong[4]").text

        # Criar um arquivo TXT com o nome do cliente
        nome_arquivo = f"{nome_cliente}.txt"
        with open(nome_arquivo, "w") as arquivo:
            arquivo.write(texto_evento)

        # Aguarde um tempo para permitir que o aplicativo processe o texto e o botão fique disponível
        time.sleep(1.8)

    except Exception as e:
        print(f"Erro ao preencher o campo de texto: {str(e)}")

def main():
    # Solicita a chave de acesso do usuário
    chave = input("Digite a chave de acesso: ")

    # Conecta ao banco de dados PostgreSQL (informações fictícias)
    try:
        conexao = psycopg2.connect(
            host="localhost",
            database="meu_database",
            user="meu_usuario",
            password="minha_senha"
        )

        # Verifica se a chave de acesso é válida
        if verificar_chave_acesso(conexao, chave):
            # Se a chave for válida, continue com o script
            login = input("Login: ")
            senha = input("Senha: ")

            # Criar Navegador
            driver = webdriver.Chrome()

            try:
                # Abra o site
                driver.get("https://adm.fullarm.com/monitoramento#!/ocorrencias")

                # Preencher o campo de login e senha
                campologin = driver.find_element(By.ID, 'username')
                campologin.send_keys(login)
                camposenha = driver.find_element(By.ID, 'password')
                camposenha.send_keys(senha)

                # Click Login
                clicklogin = driver.find_element(By.ID, 'btn_login')
                clicklogin.click()

                # Chame a função para coletar eventos
                coletar_eventos(driver)

            except Exception as e:
                print(f"Erro durante a execução: {str(e)}")
        else:
            print("Chave de acesso inválida. Encerrando o programa.")
            time.sleep(2)

    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {str(e)}")

if __name__ == "__main__":
    main()
