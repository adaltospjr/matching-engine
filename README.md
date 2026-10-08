# MatchBook

Motor de casamento de ordens (*matching engine*) com livro de ofertas (*order book*), escrito em Python. Projeto de estudo que simula o núcleo de uma bolsa de valores: receber ordens de compra e venda, mantê-las organizadas por preço e tempo, e gerar negócios (*trades*) quando elas se cruzam.

> Projeto em desenvolvimento, organizado em sprints. A estrutura e a API podem mudar.

## Funcionalidades

- **Livro de ofertas por instrumento** (ex.: `PETR4`), com lado comprador (*bids*) e vendedor (*asks*)
- **Prioridade preço-tempo**: melhor preço primeiro; no mesmo preço, a ordem mais antiga primeiro
- **Execução no preço da ordem que estava no book** (*maker*), não no da ordem que chegou
- **Matching em múltiplos níveis de preço** e execução parcial
- **Tipos de ordem**
  - `LIMIT`: executa só no preço-limite ou melhor
  - `MARKET`: executa contra a melhor oferta disponível, a qualquer preço
- **Validade (*time in force*)**
  - `GTC` (*Good 'Til Cancelled*): o que não executar fica no book
  - `IOC` (*Immediate or Cancel*): executa o que puder na hora e descarta o resto
  - `FOK` (*Fill or Kill*): executa a ordem inteira de uma vez, ou não executa nada
- **Cancelamento de ordens** e consulta de *best bid*, *best ask* e *spread*

### Regras de negócio importantes

- Ordens `MARKET` não podem ficar paradas no book: precisam ser `IOC` ou `FOK`.
- No `FOK`, o motor **verifica a liquidez antes de executar**, sem alterar o book. Um negócio fechado não pode ser desfeito, então a checagem precisa vir antes de qualquer efeito colateral.
- A regra de cruzamento (se uma ordem cruza um nível de preço) fica centralizada em um único método, `OrderBook._crosses`.

## Estrutura

```
src/matching_engine/order_book/
├── order.py         # Order, Side, OrderType, TimeInForce e validações
├── price_level.py   # Fila FIFO de ordens em um mesmo preço
├── book_side.py     # Um lado do book (bids ou asks), ordenado por preço
├── book.py          # OrderBook: entrada de ordens e motor de matching
└── trade.py         # Negócio gerado pelo casamento de duas ordens

tests/order_book/    # Testes de cada componente e do matching
```

## Exemplo de uso

```python
from matching_engine.order_book.book import OrderBook
from matching_engine.order_book.order import Order, OrderType, Side, TimeInForce

book = OrderBook(instrument="PETR4")

book.submit(Order(
    order_id="sell1", client_order_id="c-sell1",
    side=Side.SELL, order_type=OrderType.LIMIT,
    quantity=100, price=3250, time_in_force=TimeInForce.GTC,
))

trades = book.submit(Order(
    order_id="buy1", client_order_id="c-buy1",
    side=Side.BUY, order_type=OrderType.LIMIT,
    quantity=100, price=3250, time_in_force=TimeInForce.GTC,
))

print(trades[0].price, trades[0].quantity)  # 3250 100
```

## Como rodar

Requer **Python 3.13+**.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Testes com cobertura:

```bash
pytest --cov=src --cov-report=term-missing
```

## Autor

**Adalto Linhares**: [LinkedIn](https://www.linkedin.com/in/adalto-linhares/)