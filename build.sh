python -m nuitka \
    --standalone \
    --nofollow-import-to=ipython,ipywidgets,sympy,pygments \
    --include-distribution-metadata=numpy,scipy,dask,numba,libertem \
    --assume-yes-for-downloads \
    src/dearstemgui
