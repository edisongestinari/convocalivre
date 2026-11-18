# Instalar ConvocaLivre no Windows (versão 0.6.1)

O ConvocaLivre oferece uma versão Windows feita com PyInstaller e Inno Setup.
O usuário não precisa instalar Python ou executar comandos para abrir o programa.

## Baixar o instalador de teste

1. Abra a [execução validada do instalador 0.6.1](https://github.com/edisongestinari/convocalivre/actions/runs/44222710341). Para versões futuras, use https://github.com/edisongestinari/convocalivre/actions/workflows/windows_installer.yml
2. Selecione a execução recente com **Build Windows installer** concluído com sucesso.
3. Em **Artifacts**, baixe o arquivo **ConvocaLivre-Windows-Setup-0.6.1-UNSIGNED**.
4. Extraia o ZIP e confirme que contém:
   - ConvocaLivre_Setup_0_6_1.exe
   - SHA256SUMS.txt
5. Confirme o SHA-256 do instalador, em PowerShell, na pasta extraída:

~~~powershell
Get-FileHash -Algorithm SHA256 .\ConvocaLivre_Setup_0_6_1.exe
Get-Content .\SHA256SUMS.txt
~~~

Compare os 64 caracteres hexadecimais. A comparação só comprova que o arquivo
corresponde ao artefato publicado pelo workflow; **não equivale a uma assinatura
digital ou auditoria independente de segurança**.

6. Execute o instalador somente se confiar na origem e tiver avaliado as
   advertências de segurança. Ele instala em uma pasta do usuário e oferece
   atalho no menu Iniciar; o atalho da área de trabalho é opcional.

## Avisos importantes

- **Instalador sem assinatura digital**. O Windows SmartScreen pode exibir
  uma advertência sobre editor não reconhecido. Não recomendamos desativar
  o antivírus, o SmartScreen ou outras proteções de segurança.
- Distribuição inicial voltada a testes com usuários que possam verificar
  a origem do arquivo. Ainda não há suporte comercial, atualizador
  automático nem entrega automática de versões assinadas.
- O instalador utiliza permissões de usuário e não exige administrador.
  A função online consulta servidores somente após autorização explícita.
- O programa continua sendo pré-alfa e **não confirma nomeação, convocação
  ou outros efeitos jurídicos**. Confira o documento original.
- O botão de consulta à API do Querido Diário continua experimental e pode
  não responder; usar PDF por link ou pesquisa local.

## Reproduzir a compilação no GitHub

A receita de compilação está em
[windows_installer.yml](../.github/workflows/windows_installer.yml),
o inicializador em [windows_launcher.py](../packaging/windows_launcher.py)
e a definição do setup em [ConvocaLivre.iss](../packaging/ConvocaLivre.iss).

O pipeline executa testes Python, compila a interface com PyInstaller,
verifica que o executável inicializa em modo de teste e, por fim,
empacota a aplicação com Inno Setup. Ao terminar, publica instalador
e checksum por até 30 dias nos artefatos da execução.

**Limite:** o smoke test automatizado não substitui abrir, instalar e
desinstalar o produto em um Windows de usuário real. Essa aceitação ainda
precisa ser realizada antes de indicar o instalador como estável.
