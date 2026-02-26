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
		in {
			devShells.${system}.default = pkgs.mkShell {
			packages = with pkgs; [
				unstable.cmake
				unstable.gcc
				vim
				gnumake
				gdb
				tree
			];

			shellHook = ''
				echo "--- C++ Dev Environment Loaded ---"
				echo "GCC Version:   $(g++ --version | head -n 1)"
				echo "CMake Version: $(cmake --version | head -n 1)"
				set -o vi
			'';
		};
	};
}
