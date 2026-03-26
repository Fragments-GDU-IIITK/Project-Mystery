{
	description = "C++ Development Environment with CMake 4.0";
	inputs = {
		nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
		nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
	};

	outputs = { self, nixpkgs, nixpkgs-unstable }: 
		let
			system = "x86_64-linux";
			pkgs = import nixpkgs { inherit system; };
			unstable = import nixpkgs-unstable { inherit system; };
            llvmPkgs = unstable.llvmPackages_latest;
		in {
			devShells.${system}.default = unstable.mkShell.override { stdenv = llvmPkgs.stdenv; } {
			packages = with pkgs; [
				unstable.cmake
                # unstable.gcc
                llvmPkgs.clang-tools
				vim
				gnumake
				gdb
				tree
				pkg-config
				ungoogled-chromium
				tmux
                openssl

				xorg.libX11
				xorg.libX11.dev
				xorg.libXcursor.dev
				xorg.libXi.dev
				xorg.libXinerama.dev
				xorg.libXrandr.dev
				libGL.dev
			];

			shellHook = ''
				echo "--- C++ Dev Environment Loaded ---"
				echo "Clang Version:   $(clang++ --version | head -n 1)"
				echo "CMake Version: $(cmake --version | head -n 1)"
				echo "Chromium Version: $(chromium --version | head -n 1)"

				export LD_LIBRARY_PATH=${pkgs.libGL}/lib:$LD_LIBRARY_PATH
				fish
			'';
		};
	};
}
