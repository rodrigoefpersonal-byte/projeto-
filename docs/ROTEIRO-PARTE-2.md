# Parte 2: "Os Suspeitos"

**Série:** A Rachadura do Andar 12 (Parte 2/3)
**Formato:** igual à Parte 1: 9:16, cenas em 3D low-poly, legenda palavra a palavra, voz do Witalo, tom descontraído.
**Duração estimada:** ~58 s
**Mecânica da parte:** jogo de detetive. São 4 cartas de suspeito, e cada uma recebe um carimbo (INOCENTE / FORA / PARCIAL / SUSPEITO).

---

## Narração (texto pronto para a voz)

> As tags entre colchetes são instruções de entonação para a ElevenLabs e não aparecem na legenda.

```
[excited] Recapitulando: rachadura no décimo segundo andar, e o selo de gesso… partiu. Ou seja: ela tá crescendo.

[curious] A Dona Marta falou: rachadura que cresce tem quatro suspeitos. E a gente tinha 24 horas pra achar o culpado.

[excited] Suspeito número um: o chão. Se a fundação afundar, o prédio todo trinca. Mediram com o nível… zero milímetro. Inocente!

Suspeito dois: a secagem. Concreto que seca rápido demais faz umas fissurinhas. Só que elas aparecem cedo e param. A nossa não parou. Fora!

[curious] Suspeito três: o peso. Tinha uma pilha de piso em cima da laje. Ajuda a explicar… mas não explica tudo.

[nervous] Suspeito quatro: o próprio concreto. Lembra dos cilindros que eles guardam no dia da concretagem? A gente levou pra prensa… e eles quebraram antes da hora. Concreto fraco.

[curious] Mas por que fraco? Aí eu fui fuçar a nota do caminhão daquele dia. E tinha uma anotação escrita à mão…

[whispers] Água adicionada na obra.

[dramatically] E quem assinou… foi o Seu Jorge.

[excited] Parte três: o que o Seu Jorge escondia. Segue aí!
```

---

## Cenas

| # | Tempo (aprox.) | Fala | Visual 3D | Legenda / tags / HUD |
|---|---|---|---|---|
| 1 | 0–6 s | "Recapitulando… ela tá crescendo." | Montagem rápida da Parte 1: rachadura se desenhando e o selo partindo (reaproveita as cenas). | HUD **PARTE 2** no topo. Destaque em **RACHADURA** e **PARTIU** (vermelho), **CRESCENDO** (vermelho). |
| 2 | 6–12 s | "Rachadura que cresce tem quatro suspeitos… 24 horas." | Na frente da torre, 4 cartas grandes de bloco viradas de costas, com "?", girando de leve. Dona Marta aponta para elas. | Cronômetro **24:00:00** começando a correr. Destaque em **QUATRO** e **24**. |
| 3 | 12–19 s | "Suspeito número um: o chão… Inocente!" | Corte do solo (reaproveitado) com as estacas. Na superfície, um **nível de topografia** num tripé. O prédio dá uma "afundadinha" fantasma e volta. | Carta **SOLO** vira. Medidor **RECALQUE: 0 mm**. Carimbo **INOCENTE** (verde). |
| 4 | 19–27 s | "Suspeito dois: a secagem… Fora!" | Laje no sol forte, com ondas de calor (vapor saindo). Aparecem fissurinhas finas que **param** de crescer (time-lapse com relógio). | Carta **RETRAÇÃO**. Tag **SECA RÁPIDO = FISSURINHA**. Carimbo **FORA** (verde). |
| 5 | 27–33 s | "Suspeito três: o peso… não explica tudo." | Pallets de piso cerâmico empilhados na laje do 12º andar. A laje curva um pouquinho (exagero visual). Setas azuis empurrando para baixo. | Carta **SOBRECARGA**. Carimbo **PARCIAL** (amarelo). |
| 6 | 33–43 s | "Suspeito quatro: o próprio concreto… Concreto fraco." | Laboratório: prateleira com cilindros cinza etiquetados. Um cilindro vai para a **prensa hidráulica**, desce, e ele racha. O ponteiro do medidor para **antes** da linha amarela. | Tag **CORPO DE PROVA**. Medidor com linha **RESISTÊNCIA DE PROJETO**. Carta **CONCRETO** com carimbo **SUSPEITO** (vermelho). |
| 7 | 43–50 s | "Mas por que fraco?… escrita à mão…" | Escritório da obra (contêiner). Téo mexe numa pilha de papéis, puxa uma **nota do caminhão betoneira**. Zoom no papel. | Overlay 2D do papel com campos: DATA, VOLUME, **12º ANDAR**. Tag **NOTA DO CAMINHÃO**. |
| 8 | 50–54 s | "Água adicionada na obra… foi o Seu Jorge." | Close no papel: anotação manuscrita em vermelho "+ ÁGUA NA OBRA" e uma assinatura. Corte para o **Seu Jorge** (capacete laranja, rádio na mão) virando de costas devagar. | Destaque em **ÁGUA** (azul) e **JORGE** (vermelho). Tag **SEU JORGE · MESTRE DE OBRAS**. Batida grave e flash vermelho. |
| 9 | 54–58 s | "Parte três… Segue aí!" | Torre à noite, câmera girando, tela escurecida. | Cartão: **PARTE 3** / **O QUE O SEU JORGE ESCONDIA** / "SEGUE PRA NÃO PERDER". |

---

## Novos elementos 3D para construir

- **Seu Jorge:** personagem de blocos com capacete laranja, camisa cinza, rádio preto na mão e bigode (bloquinho marrom).
- **Cartas de suspeito:** placas grandes (frente colorida, verso com "?") que giram 180° para revelar o nome.
- **Carimbos** (2D, como o "VENDIDO" do estilo C): retângulo com borda grossa, levemente girado, com animação de "batida".
- **Nível de topografia:** tripé fino e caixinha amarela com lente.
- **Sol e calor:** esfera amarela grande e ondas de calor (planos transparentes ondulando).
- **Pallets de piso:** caixas bege empilhadas sobre estrados de madeira.
- **Laboratório:** bancada, prateleira de cilindros e prensa hidráulica (duas placas e colunas, com a placa de cima descendo).
- **Escritório de obra:** contêiner azul com porta, mesa e pilha de papéis.
- **Caminhão betoneira:** aparece no flashback da Parte 3, mas já pode ser modelado agora (cabine, tambor laranja girando).

## Fatos usados (conferir)

- O **recalque** (afundamento da fundação) é monitorado com nível de topografia em pontos fixos do prédio.
- **Fissuras de retração** (secagem rápida) são finas e costumam aparecer nos primeiros dias, depois estabilizam.
- **Sobrecarga** de material estocado na laje pode causar fissuras, mas o padrão costuma ser diferente.
- **Corpos de prova** são moldados no dia da concretagem e rompidos em prensa (normalmente aos 7 e aos 28 dias).
- A **nota de remessa do concreto** tem campo para registrar **água adicionada na obra**. Água a mais aumenta a relação água/cimento e reduz a resistência.

## Legenda e hashtags sugeridas

> 4 suspeitos, 24 horas: quem trincou o prédio? 🕵️ (Parte 2/3)

`#engenhariacivil #obra #curiosidades #vocesabia #misterio #fyp`
