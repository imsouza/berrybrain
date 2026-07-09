"use client";

import type { ReactNode } from "react";

export function GuidePanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/70 backdrop-blur-sm" onClick={onClose}>
      <div className="relative max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-panel p-6 shadow-2xl ring-1 ring-border/50" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold">Guia do BerryBrain</h2>
          <button className="rounded-lg p-1 text-muted hover:bg-surface hover:text-foreground" onClick={onClose}>
            <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <div className="space-y-8 text-sm text-foreground/85">
          <Step num={1} title="Comece escrevendo">
            <p>Na Home, escreva no campo de texto central. O BerryBrain cria a nota automaticamente no vault, sem precisar de título. É a forma mais rápida de capturar ideias.</p>
            <p className="mt-1 text-xs text-muted">Dica: você pode criar rascunhos vazios com o botão "Criar rascunho vazio" ou via sidebar em "Nova nota".</p>
          </Step>

          <Step num={2} title="Assimilação automática (Autopilot)">
            <p>Ao salvar uma nota, o Autopilot aciona um pipeline automático:</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-muted">
              <li><strong>Parse</strong> — extrai frontmatter, headings, links e metadados</li>
              <li><strong>Classify</strong> — IA classifica tipo, tags e termos técnicos</li>
              <li><strong>Assimilate</strong> — IA gera resumo, conceitos, gaps e perguntas</li>
              <li><strong>Embed</strong> — gera embedding vetorial para busca semântica</li>
              <li><strong>Connect</strong> — IA sugere conexões entre notas</li>
              <li><strong>Expand Graph</strong> — extrai tópicos, entidades, contexto e gera insights</li>
            </ul>
            <p className="mt-1 text-xs text-muted">O progresso aparece na Home como "Autopilot processando". Acompanhe no Monitor.</p>
          </Step>

          <Step num={3} title="Grafo de conhecimento">
            <p>O grafo transforma suas notas em uma rede viva de conhecimento:</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-muted">
              <li><strong>Brain View</strong> — visualização padrão com notas e conceitos interconectados</li>
              <li><strong>Tópicos</strong> — temas extraídos dos headings e metadados das notas</li>
              <li><strong>Entidades</strong> — termos técnicos, ferramentas e tecnologias detectadas</li>
              <li><strong>Insights</strong> — caixas de informação com padrões, lacunas e sugestões</li>
              <li><strong>Lacunas</strong> — conhecimentos faltantes que o grafo identificou</li>
            </ul>
            <p className="mt-1 text-xs text-muted">Use os filtros por tipo, status, origem e confiança. Clique em um nó para ver detalhes. Duplo clique abre a nota.</p>
          </Step>

          <Step num={4} title="Conexões e conceitos">
            <p>Na Home, as seções "Conexões recentes" e "Conceitos detectados" mostram o que o BerryBrain encontrou:</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-muted">
              <li><strong>Confirmar/Ignorar</strong> — você valida ou descarta sugestões da IA</li>
              <li><strong>Criar nota permanente</strong> — transforma um conceito em uma nota dedicada</li>
              <li><strong>Ver no grafo</strong> — visualiza a conexão no contexto do grafo</li>
              <li>Conexões confirmadas são marcadas como consolidadas; ignoradas deixam de aparecer nas sugestões</li>
            </ul>
          </Step>

          <Step num={5} title="Insights da IA">
            <p>A IA analisa seu grafo periodicamente e gera insights acionáveis:</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-muted">
              <li><strong>Lacuna detectada</strong> — conhecimento faltando que merece nota</li>
              <li><strong>Conceito recorrente</strong> — tema que aparece em várias notas</li>
              <li><strong>Nó central</strong> — nota/conceito com muitas conexões</li>
              <li><strong>Trilha sugerida</strong> — sequência lógica de estudo</li>
              <li>Cada insight tem ação sugerida: criar nota, revisar, conectar</li>
            </ul>
            <p className="mt-1 text-xs text-muted">Use "Abrir notas" para ver contexto, "Aplicar" para marcar como resolvido, "Ignorar" para descartar.</p>
          </Step>

          <Step num={6} title="Editor de notas">
            <p>O editor suporta Markdown completo com autosave:</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-muted">
              <li><strong>Wiki links</strong> — <code>[[nome da nota]]</code> cria backlinks automáticos no grafo</li>
              <li><strong>Frontmatter</strong> — metadados YAML entre <code>---</code> no topo da nota</li>
              <li><strong>Painel direito</strong> — conceitos, conexões e insights relacionados à nota atual</li>
              <li><strong>Atalhos</strong> — <kbd className="rounded bg-surface px-1 text-[10px]">Ctrl+S</kbd> salva, <kbd className="rounded bg-surface px-1 text-[10px]">Ctrl+K</kbd> abre busca rápida</li>
            </ul>
          </Step>

          <Step num={7} title="Configuração de IA">
            <p>Nas Configurações (ícone de engrenagem no canto inferior esquerdo):</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-muted">
              <li><strong>Provedor de IA</strong> — principal: classificação, assimilação, embeddings (cloud ou local)</li>
              <li><strong>IA do Grafo</strong> — inferência e expansão do grafo (herda do principal se vazio)</li>
              <li><strong>Cloud</strong> — NVIDIA NIM, OpenAI, ou qualquer API compatível com OpenAI</li>
              <li><strong>Local</strong> — Ollama (requer servidor Ollama rodando)</li>
              <li>Configure API URL, API Key e modelo separadamente por provedor</li>
            </ul>

            <div className="mt-3 rounded-xl bg-surface p-3 ring-1 ring-border/35">
              <div className="text-xs font-semibold mb-2">Modelos cloud recomendados</div>
              <div className="space-y-2 text-xs text-muted">
                <div>
                  <div className="font-medium text-foreground/80">NVIDIA NIM</div>
                  <div className="mt-0.5 grid grid-cols-2 gap-x-4 gap-y-0.5">
                    <span><strong>qwen/qwen3.5-397b-a17b</strong></span><span className="text-muted/60">Raciocínio profundo, insights de grafo</span>
                    <span><strong>qwen/qwen3.5-32b-a17b</strong></span><span className="text-muted/60">Assimilação, classificação, embeddings</span>
                    <span><strong>meta/llama-3.3-70b-instruct</strong></span><span className="text-muted/60">Geração de títulos e conexões</span>
                    <span><strong>nvidia/nv-embedqa-e5-v5</strong></span><span className="text-muted/60">Embeddings vetoriais</span>
                  </div>
                </div>
                <div className="border-t border-border/30 pt-2">
                  <div className="font-medium text-foreground/80">OpenAI / Compatíveis</div>
                  <div className="mt-0.5 grid grid-cols-2 gap-x-4 gap-y-0.5">
                    <span><strong>gpt-4o</strong></span><span className="text-muted/60">Uso geral, alta qualidade</span>
                    <span><strong>gpt-4o-mini</strong></span><span className="text-muted/60">Rápido, baixo custo</span>
                    <span><strong>text-embedding-3-large</strong></span><span className="text-muted/60">Embeddings</span>
                  </div>
                </div>
                <div className="border-t border-border/30 pt-2">
                  <div className="font-medium text-foreground/80">DeepSeek</div>
                  <div className="mt-0.5 grid grid-cols-2 gap-x-4 gap-y-0.5">
                    <span><strong>deepseek-chat</strong></span><span className="text-muted/60">Raciocínio e análise</span>
                    <span><strong>deepseek-reasoner</strong></span><span className="text-muted/60">Insights complexos de grafo</span>
                  </div>
                </div>
              </div>
              <p className="mt-2 text-[10px] text-muted/50">Modelos locais (Ollama) dependem do seu hardware. Escolha conforme VRAM disponível.</p>
            </div>
          </Step>

          <Step num={8} title="Vault e sincronização">
            <p>O vault é uma pasta de arquivos Markdown:</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-muted">
              <li>Arquivos <code>.md</code> no diretório vault são detectados automaticamente</li>
              <li>Use "Scan vault" para forçar uma varredura completa</li>
              <li>Notas criadas pelo BerryBrain também aparecem como arquivos no vault</li>
              <li>Compatível com Obsidian — edite com qualquer editor Markdown</li>
            </ul>
          </Step>

          <Step num={9} title="Monitor e Jobs">
            <p>O Monitor (acessível pela Home ou sidebar) mostra:</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-muted">
              <li><strong>Worker status</strong> — se o processador está online e saudável</li>
              <li><strong>Jobs ativos</strong> — tarefas em execução com tempo decorrido</li>
              <li><strong>Fila</strong> — jobs pendentes aguardando processamento</li>
              <li><strong>Erros</strong> — jobs que falharam com mensagem de erro</li>
              <li>O worker processa até 4 jobs simultâneos com retry automático</li>
            </ul>
          </Step>

          <Step num={10} title="Dicas rápidas">
            <ul className="list-inside list-disc space-y-0.5 text-xs text-muted">
              <li>Escreva sem medo — o BerryBrain organiza depois</li>
              <li>Use <code>[[links wiki]]</code> para conectar notas manualmente</li>
              <li>Confirme ou ignore sugestões para treinar o que é relevante</li>
              <li>O grafo fica mais rico conforme você escreve mais</li>
              <li>IA cloud (NVIDIA NIM) é mais rápida e precisa que Ollama local</li>
              <li>Se algo não aparecer no grafo, clique em "Recalcular conexões" na Home</li>
            </ul>
          </Step>
        </div>

        <div className="mt-6 border-t border-border/50 pt-4 text-center">
          <button className="rounded-xl bg-accent px-4 py-2 text-xs font-medium text-white" onClick={onClose}>Entendi</button>
        </div>
      </div>
    </div>
  );
}

function Step({ num, title, children }: { num: number; title: string; children: ReactNode }) {
  return (
    <div>
      <div className="mb-1 flex items-center gap-2">
        <span className="grid size-5 place-items-center rounded-full bg-accent text-[10px] font-bold text-white">{num}</span>
        <h3 className="text-sm font-semibold">{title}</h3>
      </div>
      <div className="ml-7">{children}</div>
    </div>
  );
}
