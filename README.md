[https://dimensionador-solar.streamlit.app/](https://dimensionador-fotovoltaico-sigilos-ahu4vpgxku2e7fvmuz7nwg.streamlit.app/)

## Como Alimentar a Planilha

Apenas colaboradores autorizados podem atualizar a base de dados. O sistema lê as informações diretamente do arquivo Excel na raiz do projeto.

Siga o passo a passo abaixo para instalar as ferramentas necessárias e atualizar a planilha com segurança.

### 1️⃣ Instalação do Git
Se você ainda não tem o Git instalado no seu computador:
* **Windows:** Baixe e instale o [Git for Windows](https://git-scm.com). Durante a instalação, pode avançar clicando em "Next" mantendo as opções padrão.
* **Mac:** Abra o terminal e digite `git --version` (se não tiver, o próprio sistema solicitará a instalação).
* **Linux:** Rode o comando `sudo apt install git` (para distribuições baseadas em Debian/Ubuntu).

### 2️⃣ Configuração Inicial (Apenas na primeira vez)
Abra o Git Bash e configure sua identidade para que o GitHub reconheça seus envios:
```bash
git config --global user.name "Seu Nome Completo"
git config --global user.email "seu-email-do-github@exemplo.com"
```

### 3️⃣ Clonando o Repositório
Escolha ou crie uma pasta que ficara o repositório (NÃO PODE SER NO GOOGLE DRIVE)
Abra o git bash dentro dessa pasta
<img width="845" height="455" alt="image" src="https://github.com/user-attachments/assets/76672f90-7096-4984-ba0e-02f0c7c638ea" />

digite o seguinte código
```
git clone https://github.com/EnzoAndradeF/dimensionador-fotovoltaico-sigiloso.git
```

---

## 🔄 Fluxo de Atualização da Planilha

Toda vez que você precisar atualizar os dados, siga estritamente estes **4 passos**:

### Passo 1: Atualize seu computador antes de mexer
Abra o terminal na pasta do repositório
<img width="865" height="510" alt="image" src="https://github.com/user-attachments/assets/237ee72f-5577-4891-9a1c-ebf4bb3ca171" />

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
**Assim que o `git push` for concluído, dentro do link da aplidação cique nos 3 pontinhos no canto superior direito e limpe o cache, em seguida reinicie a página**

## 🚨 O que fazer se o `git push` for rejeitado? (Esqueceu o `git pull`)

Se você tentou rodar `git push origin main` e recebeu uma mensagem de erro informando que o envio foi rejeitado (`! [rejected]`), significa que **outra pessoa enviou alterações para o GitHub antes de você** e você esqueceu de rodar o `git pull` no Passo 1.

Para evitar conflitos de versão ou ter que resolver problemas no código, **a melhor opção é fazer um backup da sua planilha, resetar o repositório local com a versão atual da nuvem e colar sua planilha atualizada por cima**.

### Siga este passo a passo para destravar:

1. **Crie uma cópia de segurança da sua planilha:**  
   Copie o arquivo `calculo_mppt.xlsx` e cole em outra pasta fora do repositório (ex: na sua *Área de Trabalho*) para não perder os dados que você alterou.

2. **Resete o repositório local:**  
   Execute os dois comandos abaixo no Git Bash para ignorar as alterações locais e sincronizar exatamente com o GitHub:
   ```bash
   git fetch origin
   git reset --hard origin/main
   ```
3. **Restaure sua planilha e envie novamente:**
    Copie o arquivo calculo_mppt.xlsx que você salvou na Área de Trabalho e cole de volta na pasta do projeto (substituindo o arquivo existente).
    Execute o envio normalmente:
    ```
    git add calculo_mppt.xlsx
    git commit -m "💡 util: Adicionando dados atualizados"
    git push origin main
    ```