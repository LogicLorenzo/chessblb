// src/server.js
import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

const app  = express();
const PORT = 8000;

// fix __dirname in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);

// serve everything in public/ at http://localhost:8000/
app.use(express.static(path.join(__dirname, '../public')));

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});