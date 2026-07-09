# Arquitetura inicial

## Camadas

- `packages/domain`: regras puras de negocio.
- `packages/application`: casos de uso.
- `packages/infrastructure`: implementacoes concretas.
- `apps/api`: interface HTTP e orquestracao de jobs.
- `apps/web`: interface do usuario.
- `apps/worker`: processamento pesado e chamadas ao Ollama local.

## Fluxo obrigatorio de IA

```txt
Usuario altera nota
File watcher detecta mudanca
API cria job
Worker processa job
Worker chama Ollama local
Resultado volta para API/dados
Interface mostra o resultado
```

## Invariantes

- Notas originais ficam em Markdown no `vault/`.
- Metadados automaticos ficam separados da nota original.
- Automacoes devem gerar log.
- Alteracoes automaticas precisam ser reversiveis sempre que possivel.
- Nada deve depender de cloud para funcionar.
