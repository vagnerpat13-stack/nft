# Agente Professor de Matemática — Rede Estadual MG

Sistema de apoio para planejamento de aulas de **Matemática** no **ensino médio** da **SEE/MG**, com foco em estudantes com **dificuldade de aprendizagem** em **contexto rural**, alinhado ao **CRMG**, **Planos de Curso 2026** e avaliações **Simave**.

## Como usar no Cursor

1. O skill **`professor-matematica-mg`** é carregado automaticamente em `.cursor/skills/`.
2. Peça planos citando série e tema, por exemplo:
   - *"Plano de 50 min para função afim, 1º ano, turma com baixo desempenho em gráficos."*
   - *"Simulado estilo Simave para trigonometria, 2º ano."*
3. Copie `dados/professor.template.json` para `dados/professor.json` e preencha percentuais da diagnóstica e da 1ª trimestral para planos personalizados.

## Estrutura do repositório

```
.cursor/skills/professor-matematica-mg/   # Instruções do agente
conhecimento/                            # Base SEE/MG, Simave, por série
templates/plano-aula-50min.md            # Modelo de aula
exemplos/                                # Planos prontos (amostra)
dados/professor.template.json            # Seus dados de turma
trade-bot/                               # Robô de trade adaptativo (backtest)
```

## Situação letiva considerada (2026)

| Marco | Período |
|-------|---------|
| Avaliação Diagnóstica | Fevereiro/2026 |
| 1ª Avaliação Trimestral | 25/05 a 03/06/2026 |
| **2º trimestre** | Em andamento — preparação para **2ª trimestral** |

## Conteúdos por série (configuração do professor)

| Série | Foco no 2º trimestre |
|-------|----------------------|
| 1º ano | Funções (afim, quadrática, modelagem) |
| 2º ano | Trigonometria |
| 3º ano | Geometria analítica |

## Referências oficiais

- [Planos de Curso CRMG](https://curriculoreferencia.educacao.mg.gov.br/index.php/plano-de-cursos-crmg)
- [Portal das Avaliações — Simave](https://avaliacoes.educacao.mg.gov.br/)
- [Planos 2026 (download)](https://planos.professormg.com.br/)

## Licença e uso

Material de apoio pedagógico; documentos oficiais permanecem propriedade da SEE/MG. Resumos e sequências aqui não substituem memorandos e orientadores da escola/SRE.
