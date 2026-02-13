cask "espin" do
  version "1.0.0"
  sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"

  url "https://github.com/ujj/espin/archive/refs/tags/v#{version}.tar.gz"
  name "Espin"
  desc "Local streaming ASR for macOS — voice to text, types into focused app"
  homepage "https://github.com/ujj/espin"

  depends_on formula: "espin"

  stage_only true

  postflight do
    app_source = Formula["espin"].opt_libexec/"espin.app"
    app_target = appdir/"Espin.app"
    FileUtils.rm_rf app_target if app_target.exist?
    FileUtils.cp_r app_source, app_target
  end

  uninstall delete: ["#{appdir}/Espin.app"]

  caveats <<~EOS
    Espin is installed in Applications. Double-click to launch.
    Grant Accessibility and Microphone to "Espin" in System Settings → Privacy & Security.
  EOS
end
