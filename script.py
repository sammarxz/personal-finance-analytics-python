import json
import ofxparse
import pandas as pd
import os
from datetime import datetime
from tqdm import tqdm
import requests

df = pd.DataFrame()

def parse_ofx_file(filepath):
    try:
        with open(filepath, encoding="ISO-8859-1") as ofx_file:
            ofx = ofxparse.OfxParser.parse(ofx_file)
            
        transactions_data = []
        for account in ofx.accounts:
            for transaction in account.statement.transactions:
                transactions_data.append({
                    "Data": transaction.date,
                    "Valor": float(transaction.amount),
                    "Descrição": transaction.memo,
                    "ID": transaction.id                          
                })
        return pd.DataFrame(transactions_data)
    except (ValueError, AttributeError) as e:
        print(f"Error processing {filepath}: {str(e)}")
        return pd.DataFrame()


df = pd.DataFrame()
for extrato in os.listdir("extratos"):
    df_temp = parse_ofx_file(f"extratos/{extrato}")
    if not df_temp.empty:
        df = pd.concat([df, df_temp], ignore_index=True)

df["Data"] = pd.to_datetime(df["Data"]).dt.date


# LLM
def categorize_transaction(text, model="llama3.2"):
    prompt = f"""
    você é um analista de dados, trabalhando em um projeto de limpeza de dados. Seu trabalho é escolher uma categoria adequada para cada lançamento financeiro que vou te enviar.
    Todas as transações financeiras  são de uma pessoa física.
    Escolha uma dentre as seguintes categorias:
        - Alimentação
        - Receitas
        - Saúde
        - Mercado
        - Educação
        - Compras
        - Construção
        - Investimentos
        - Transferência para terceiros 
        - Internet
        - Moradia
        - Transporte

    Escolha a categoria desse item:
    {text}

    Responda apenas com a categoria."""

    r = requests.post(
        "http://0.0.0.0:11434/api/chat",
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False}
    )

    r.raise_for_status()

    response = json.loads(r.text)
    return response["message"]["content"].strip()

# Add categories to the DataFrame
df['Categoria'] = None
for idx in tqdm(df.index, desc="Categorizando transações"):
    description = df.loc[idx, 'Descrição']
    category = categorize_transaction(description)
    df.loc[idx, 'Categoria'] = category

# Save categorized data
df.to_csv('transacoes_categorizadas.csv', index=False)

