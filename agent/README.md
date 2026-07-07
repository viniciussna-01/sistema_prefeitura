# Agente Desktop — Sistema Prefeitura

Consulte a documentação completa em [`../docs/agente.md`](../docs/agente.md).

```powershell
pip install -e .
sistema-agent --enroll <TOKEN> --api https://api.suaempresa.com.br
sistema-agent   # roda na bandeja do sistema
```

Testes: `python -m pytest`
Build do executável: `pip install pyinstaller && pyinstaller build.spec`
