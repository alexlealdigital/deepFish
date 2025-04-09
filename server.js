const express = require('express');
const { Pool } = require('pg');
require('dotenv').config(); // Carrega variáveis do .env (apenas para desenvolvimento)

const app = express();
app.use(express.json());

// Configuração do PostgreSQL (Render ou local)
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: {
    rejectUnauthorized: false // Necessário para o Render
  }
});

// Rota para incrementar jogadas
app.post('/incrementar-jogadas', async (req, res) => {
  const { nomeVariavel } = req.body;

  try {
    const result = await pool.query(
      `UPDATE jogadas SET valor = valor + 1 WHERE nome = $1 RETURNING valor`,
      [nomeVariavel]
    );

    if (result.rowCount === 0) {
      return res.status(404).json({ erro: "Variável não encontrada" });
    }

    res.json({ 
      sucesso: true, 
      jogadas: result.rows[0].valor 
    });

  } catch (erro) {
    console.error("Erro no PostgreSQL:", erro);
    res.status(500).json({ erro: "Falha ao atualizar jogadas" });
  }
});

// Health check (opcional para Render)
app.get('/', (req, res) => {
  res.send('API de Jogadas Online');
});

// Inicia o servidor
const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
  console.log(`API rodando na porta ${PORT}`);
  console.log(`Modo: ${process.env.NODE_ENV || 'development'}`);
});
