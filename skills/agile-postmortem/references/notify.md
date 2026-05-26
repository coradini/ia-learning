# Notificação: Google Chat + Teams (passo 6)

Objetivo: avisar, nos canais ao mesmo tempo, que há um novo post mortem pronto.

## Google Chat (mesmo canal da família agile-*)
A notificação do Google Chat usa um **incoming webhook**, cuja URL fica na
variável `GCHAT_WEBHOOK_URL` do `.env` compartilhado (`~/.config/agile/.env`) — a
mesma usada pela `agile-report-bugs`. Reusar essa variável = postar no **mesmo
espaço** do Google Chat. Não embuta a URL; carregue o `.env` existente.

## Antes de enviar
Enviar mensagem é uma ação sensível. **Sempre** mostre o texto final e os destinos
e peça confirmação explícita no chat antes de disparar. Nunca envie automaticamente.

## Mensagem (modelo)
```
📄 Novo post mortem pronto: <título>
Data do incidente: <data>
Resumo: <1 linha>
Documento: <link>
```

## Como enviar (script bundlado)
`scripts/notify.py` (só usa biblioteca padrão, sem dependências) posta no Google
Chat e, se configurado, no Teams:

```bash
# .env compartilhado → mesma webhook → mesmo canal do Google Chat
set -a; source ~/.config/agile/.env; set +a

python3 scripts/notify.py --message-file /tmp/pm_msg.txt
# só Google Chat:
python3 scripts/notify.py --message-file /tmp/pm_msg.txt --gchat-only
```
O script faz `POST {"text": "<mensagem>"}` para cada webhook e reporta sucesso/
falha por canal.

## Teams
Não há conector de envio para o Teams (o "Microsoft 365" só faz busca). Use um
**incoming webhook** do canal, na variável `TEAMS_WEBHOOK_URL` (no mesmo
`~/.config/agile/.env`). Sem ela, `notify.py` pula o Teams e avisa. Se o usuário só
quer Google Chat, use `--gchat-only`.

## Observações
- O disparo do POST depende de o ambiente permitir egress de rede para os hosts
  dos webhooks (chat.googleapis.com / outlook.office.com).
- Se nenhum webhook estiver disponível, entregue a mensagem pronta (com o link)
  para a pessoa colar nos canais e diga o que falta configurar.
