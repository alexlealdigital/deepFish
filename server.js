const express = require('express');
const { Pool } = require('pg');
const app = express();
app.use(express.json());

// Conexão com o PostgreSQL (Render)
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false } // Obrigatório para Render
});

// Rota para incrementar jogadas
app.post('/incrementar-jogadas', async (req, res) => {
  const { nomeVariavel } = req.body;

  try {
    const result = await pool.query(
      `UPDATE jogadas SET valor = valor + 1 WHERE nome = $1 RETURNING valor`,
      [nomeVariavel]
    );
    res.json({ sucesso: true, jogadas: result.rows[0].valor });
  } catch (erro) {
    res.status(500).json({ erro: erro.message });
  }
});

// Inicia o servidor
const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`API rodando na porta ${PORT}`));