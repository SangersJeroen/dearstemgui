python -m nuitka \
    --full-compat \
    --standalone \
    --enable-plugin=no-qt \
    --nofollow-import-to=ipython,ipywidgets,sympy,pygments \
    --include-distribution-metadata=numpy,scipy,dask,numba,libertem \
    --assume-yes-for-downloads \
    src/dearstemgui
