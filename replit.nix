{pkgs}: {
  deps = [
    pkgs.glibcLocales
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.glibcLocales
      pkgs.xsimd
      pkgs.libxcrypt
    ];
  };
}
