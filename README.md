# Monitor CP

Painel para consulta de comboios da CP em tempo real. Feito com `Python` e `NiceGUI`.

## Funcionalidades

-   **Pesquisa de Estações:** Permite pesquisar por qualquer estação de comboios.
-   **Agrupamento por Plataforma:** A informação dos comboios é agrupada por plataforma.
-   **Layout Responsivo:** A interface funciona em `desktop` e `mobile`.
-   **Filtros Dinâmicos:** Filtros por tipo de serviço e número de comboio com atualização em tempo real.
-   **Auto-Refresh:** Os dados são atualizados de 30 em 30 segundos.

## Como Executar

1.  **Criar ambiente virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Instalar dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Executar a aplicação:**
    ```bash
    python3 main.py
    ```

A aplicação fica disponível em `http://localhost:8080`.
