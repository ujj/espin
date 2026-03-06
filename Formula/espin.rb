class Espin < Formula
  desc "Local Streaming ASR for Coding Agents on macOS"
  homepage "https://github.com/ujj/espin"
  url "https://github.com/ujj/espin/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "b0e289fa04103f2b5f8236e87ed6b49a2acf78031d26e24195eddb1e87764bf7"
  license "MIT"

  depends_on "python@3.11"
  depends_on "uv"

  def install
    libexec.install "espin_gui.py", "pyproject.toml", "uv.lock", "README.md"
    libexec.install "espin"

    (bin/"espin-gui").write <<~SH
      #!/bin/bash
      exec "#{libexec}/.venv/bin/espin-gui" "$@"
    SH

    (bin/"espin").write <<~SH
      #!/bin/bash
      exec "#{libexec}/.venv/bin/espin" "$@"
    SH
  end

  def post_install
    cd libexec do
      system "uv", "sync", "--no-cache"
    end

    ohai "Downloading Whisper model (~1.5 GB, first time only)..."
    system libexec/".venv/bin/python", "-c",
      "from huggingface_hub import snapshot_download; snapshot_download('mlx-community/whisper-medium')"
  end

  def caveats
    <<~EOS
      To start Espin:
        espin-gui

      Then press Ctrl+Option+Space to toggle recording.

      Permissions: Grant your terminal app (Terminal, WezTerm, iTerm, etc.)
      Accessibility and Microphone access in:
        System Settings → Privacy & Security
    EOS
  end

  test do
    system (libexec/".venv/bin/python"), "-c", "import espin; import espin.main"
  end
end
