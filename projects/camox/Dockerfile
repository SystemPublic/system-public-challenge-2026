# CAMOX on a Hugging Face Space (Docker SDK). Secrets come from the Space settings, never from the image.
FROM python:3.12-slim
RUN useradd -m -u 1000 user && mkdir -p /home/user/app/data && chown -R user /home/user/app
USER user
WORKDIR /home/user/app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY --chown=user . .
ENV PATH=/home/user/.local/bin:$PATH GRAPH_DB=data/graph.duckdb
EXPOSE 7860
# Fetch the local graph copy from the private dataset on first start, then serve.
CMD python -c "import os; from huggingface_hub import hf_hub_download as get; p = os.environ['GRAPH_DB']; os.path.exists(p) or get(os.environ['GRAPH_DATASET'], 'graph.duckdb', repo_type='dataset', token=os.environ.get('HF_TOKEN'), local_dir=os.path.dirname(p))" \
    && uvicorn server.main:app --host 0.0.0.0 --port 7860
