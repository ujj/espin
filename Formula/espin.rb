class Espin < Formula
  desc "Local Streaming ASR for Coding Agents on macOS"
  homepage "https://github.com/ujj/espin"
  url "https://github.com/ujj/espin/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
  license "MIT"

  depends_on "python@3.11"
  depends_on "uv"

  def install
    # Install project files into libexec so the .app launcher can find them
    # (launcher resolves "project root" = 3 dirnames up from espin.app/Contents/MacOS/espin = libexec)
    libexec.install "espin_gui.py", "pyproject.toml", "uv.lock", "README.md"
    libexec.install "espin"
    libexec.install "espin.app"

    # Create .venv and install dependencies in libexec (no user uv needed)
    system "uv", "sync", chdir: libexec

    # CLI: symlink venv scripts so `espin` and `espin-gui` work from terminal
    bin.install_symlink (libexec/".venv/bin/espin") => "espin"
    bin.install_symlink (libexec/".venv/bin/espin-gui") => "espin-gui"

    # Symlink app for `open espin.app` from prefix
    bin.install_symlink libexec/"espin.app" => "espin.app"
  end

  def caveats
    <<~EOS
      Espin requires Accessibility and Microphone permissions.
      After installing, open Espin (double-click or: open espin.app).
      In System Settings → Privacy & Security, grant:
      - Accessibility (for typing transcribed text)
      - Microphone (for recording)
      to "Espin".
    EOS
  end

  test do
    system (libexec/".venv/bin/python"), "-c", "import espin; import espin.main"
  end
end
