"""J.A.R.V.I.S. entry point.

    python main.py             voice + HUD window (say "Jarvis ...")
    python main.py --no-gui    voice only, in the terminal
    python main.py --text      keyboard only, in the terminal
    python main.py --no-wake   skip the wake word, always listening
"""
import argparse


def main():
    ap = argparse.ArgumentParser(description="J.A.R.V.I.S. personal assistant")
    ap.add_argument("--text", action="store_true", help="type instead of speaking")
    ap.add_argument("--no-gui", action="store_true", help="don't open the HUD window")
    ap.add_argument("--no-wake", action="store_true", help="don't require the wake word")
    args = ap.parse_args()

    from jarvis.core import Jarvis

    hud = None
    if not args.text and not args.no_gui:
        try:
            from jarvis.hud import HUD
            hud = HUD()
        except Exception as e:  # no display / no tkinter
            print(f"[HUD disabled: {e}]")

    jarvis = Jarvis(text_mode=args.text, hud=hud, require_wake=not args.no_wake)
    if hud:
        hud.on_submit = jarvis.typed.put
        hud.on_close = jarvis.shutdown
        hud.run(jarvis.run)
    else:
        try:
            jarvis.run()
        except KeyboardInterrupt:
            jarvis.shutdown()


if __name__ == "__main__":
    main()
