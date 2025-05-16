# oddspedia_surebets_playwright.py
# Script para extrair sure bets do Oddspedia usando Playwright com modo stealth
# Requisitos: pip install playwright
# Para instalar navegadores: playwright install

from playwright.sync_api import sync_playwright
import time
import csv

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
        )
        page = context.new_page()
        page.goto('https://oddspedia.com/br/apostas-certas', timeout=60000)

        print('Se aparecer um desafio de captcha, resolva manualmente e pressione Enter aqui para continuar...')
        input('Pressione Enter após resolver o captcha e a página carregar completamente...')

        # NOVO: Clica no botão "Mostre mais" até não existir mais
        while True:
            try:
                btn = page.query_selector('button:has-text("Mostre mais")')
                if btn:
                    print('Clicando em "Mostre mais"...')
                    btn.click()
                    time.sleep(2)  # Aguarda carregar novos jogos
                else:
                    print('Nenhum botão "Mostre mais" encontrado. Todos os jogos carregados.')
                    break
            except Exception as e:
                print('Erro ao clicar em "Mostre mais":', e)
                break

        # Salva o HTML carregado para debug
        with open('debug_playwright.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
        print('HTML salvo em debug_playwright.html')

        # Aguarda o container principal das sure bets aparecer (mais robusto que 'table')
        page.wait_for_selector('.btools-match, .btools-match-teams', timeout=60000)
        time.sleep(2)

        # Extrai as linhas da tabela
        rows = page.query_selector_all('table tbody tr')
        print(f'Encontradas {len(rows)} sure bets na página.')
        dados = []
        for row in rows:
            cols = row.query_selector_all('td')
            if len(cols) < 5:
                continue
            evento = cols[0].inner_text().strip()
            mercado = cols[1].inner_text().strip()
            odd1 = cols[2].inner_text().strip()
            odd2 = cols[3].inner_text().strip()
            lucro = cols[4].inner_text().strip()
            print(f'Evento: {evento} | Mercado: {mercado} | Odd1: {odd1} | Odd2: {odd2} | Lucro: {lucro}')
            dados.append([evento, mercado, odd1, odd2, lucro])
        # Salva em CSV
        with open('surebets_oddspedia.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Evento', 'Mercado', 'Odd1', 'Odd2', 'Lucro'])
            writer.writerows(dados)
        print('Dados salvos em surebets_oddspedia.csv')
        
        # Aguarda o elemento que contenha 'btools' em id ou class
        try:
            btools_elem = page.wait_for_selector('[id*=btools], [class*=btools]', timeout=60000)
            print('Elemento btools encontrado!')
            # Salva o HTML do elemento para análise
            with open('btools_element.html', 'w', encoding='utf-8') as f:
                f.write(btools_elem.inner_html())
            print('HTML do elemento btools salvo em btools_element.html')
        except Exception as e:
            print('Elemento btools não encontrado na página.')
        
        # Aguarda o elemento com a classe 'btools-match-teams' aparecer
        try:
            page.wait_for_selector('.btools-match-teams', timeout=60000)
            print('Elemento .btools-match-teams encontrado!')
            # Extrai todos os elementos com essa classe
            teams_elements = page.query_selector_all('.btools-match-teams')
            print(f'Encontrados {len(teams_elements)} elementos com a classe btools-match-teams.')
            # Salva o texto de cada elemento em um arquivo para análise
            with open('btools_match_teams.txt', 'w', encoding='utf-8') as f:
                for elem in teams_elements:
                    text = elem.inner_text().strip()
                    print(text)
                    f.write(text + '\n---\n')
            print('Dados salvos em btools_match_teams.txt')
        except Exception as e:
            print('Elemento .btools-match-teams não encontrado na página.')
        
        browser.close()

if __name__ == '__main__':
    main()

# Instruções:
# 1. Instale as dependências: pip install playwright
# 2. Instale os navegadores: playwright install
# 3. Execute: python oddspedia_surebets_playwright.py
# 4. Se aparecer captcha, resolva manualmente e pressione Enter no terminal.
# 5. O script exibirá as sure bets encontradas no console e as salvará em um arquivo CSV.
