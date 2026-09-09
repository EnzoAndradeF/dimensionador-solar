https://dimensionador-fotovoltaico-sigilos-ahu4vpgxku2e7fvmuz7nwg.streamlit.app/

## Como Alimentar a Planilha

Como o repositório é privado, apenas colaboradores autorizados podem atualizar a base de dados. O sistema lê as informações diretamente do arquivo Excel na raiz do projeto.

Siga o passo a passo abaixo para instalar as ferramentas necessárias e atualizar a planilha com segurança.

### 1️⃣ Instalação do Git
Se você ainda não tem o Git instalado no seu computador:
* **Windows:** Baixe e instale o [Git for Windows](https://git-scm.com). Durante a instalação, pode avançar clicando em "Next" mantendo as opções padrão.
* **Mac:** Abra o terminal e digite `git --version` (se não tiver, o próprio sistema solicitará a instalação).
* **Linux:** Rode o comando `sudo apt install git` (para distribuições baseadas em Debian/Ubuntu).

### 2️⃣ Configuração Inicial (Apenas na primeira vez)
Abra o seu terminal (ou Git Bash no Windows) e configure sua identidade para que o GitHub reconheça seus envios:
```bash
git config --global user.name "Seu Nome Completo"
git config --global user.email "seu-email-do-github@exemplo.com"
```

### 3️⃣ Clonando o Repositório
Crie uma pasta onde vai ficar armazenado o repositório
Dentro dessa pasta, abra o terminal de comando digite o seguinte código
```
git clone https://github.com
```

---

## 🔄 Fluxo de Atualização da Planilha

Toda vez que você precisar atualizar os dados, siga estritamente estes **4 passos**:

### Passo 1: Atualize seu computador antes de mexer
Abra o terminal na pasta do repositório
Para garantir que você tem a planilha mais recente e não apagar o trabalho de outra pessoa, rode:
```bash
git pull origin main
```

### Passo 2: Altere a Planilha
Abra o arquivo **`calculo_mppt.xlsx`** no seu computador.
* ⚠️ **Regra de Ouro:** Nunca altere o nome do arquivo, o nome das colunas ou a ordem delas. O sistema depende exatamente desses nomes para funcionar.
* Salve e feche o arquivo.

### Passo 3: Prepare o arquivo para o envio
Avise o Git que você alterou o arquivo:
```bash
git add calculo_mppt.xlsx
```

### Passo 4: Salve e envie para a nuvem
Grave a sua alteração com uma mensagem explicativa e envie para o GitHub:
```bash
git commit -m "💡 util: Adicionando Renepv 605"
git push origin main
```
*Assim que o `git push` for concluído, a aplicação hospedada atualizará os dados automaticamente!*
