// app.js

const initial_FEN = "r2qr1k1/1ppb1pp1/1p1p1nnp/1P2p3/2PPP3/P4N1P/1B3PP1/R2QRBK1 w - - 1 18"
const game  = new Chess(initial_FEN);               // Chess is now available
const board = Chessboard('myBoard', {
  draggable: true,
  position: initial_FEN, 
  pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png',
  onDragStart, onDrop, onSnapEnd
});
const clock = new ChessClock(
  5 * 60,
  2,
  (color, sec) => {
    // update your UI, e.g.:
    document.getElementById(color + 'Time').textContent = formatTime(sec);
  },
  (flagged) => {
    alert(`${flagged} has flagged!`);
  }
);

const $status = $('#status');
const $fen    = $('#fen');
const $pgn    = $('#pgn');

updateStatus();
clock.onTick('white', clock.timeLeft('white'));
clock.onTick('black', clock.timeLeft('black'));


function onDragStart(src, piece) {
  if (game.isGameOver()) return false;
  if ((game.turn() === 'w' && piece[0] === 'b') ||
      (game.turn() === 'b' && piece[0] === 'w')) {
    return false;
  }
  // Highlight possible moves
  const moves = game.moves({ square: src, verbose: true });
  highlightSquares(moves.map(m => m.to));
}

function highlightSquares(squares) {
  squares.forEach(sq => {
    $('#myBoard .square-' + sq).addClass('highlight1-32417');
  });
}

function removeHighlights() {
  $('#myBoard .square-55d63').removeClass('highlight1-32417');
}

function onSnapEnd() {
  board.position(game.fen());
  removeHighlights();
}

function onDrop(src, tgt) {
  let move;
  try {
    move = game.move({ from: src, to: tgt, promotion: 'q' });
  } catch (err) {
    return 'snapback'; // Handles thrown errors
  }
  if (!move) return 'snapback'; // Handles null returns
  updateStatus();
  if (game.history().length === 1) {
    // first white move -> start Black's clock
    clock.start('black');
  } else {
    clock.switch();
  };
  if (game.isGameOver()){
    clock.stop();
  }
}


function updateStatus() {
  const turn = game.turn() === 'w' ? 'White' : 'Black';
  // game ending logic here 
  let msg   = game.isCheckmate()
              ? `Game over, ${turn} is in checkmate.`
              : game.isStalemate()
                ? 'Game over, drawn position.'
                : `${turn} to move${game.inCheck() ? ', in check!' : ''}`;
  
  $status.text(msg);
  $fen.text(game.fen());
  $pgn.text(game.pgn());
}

$('#undoBtn').on('click', function() {
  game.undo();
  board.position(game.fen());
  updateStatus();
});