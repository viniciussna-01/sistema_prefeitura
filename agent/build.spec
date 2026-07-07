# PyInstaller spec — gera o executável Windows do agente.
# Uso: pyinstaller build.spec

a = Analysis(
    ["sistema_agent/__main__.py"],
    pathex=["."],
    hiddenimports=["pystray._win32"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="SistemaPrefeituraAgent",
    console=False,
    icon=None,
    upx=True,
)
