"""Eyes: describe the screen or the webcam with Claude."""
import io

from ..router import skill


@skill(r"\b(?:what(?:'s| is)(?: on)? (?:my )?screen|look at (?:my )?screen|read (?:my )?screen|"
       r"describe (?:my )?screen|analy[sz]e (?:my )?screen|what am i looking at)\b")
def screen(m, ctx):
    import pyautogui
    img = pyautogui.screenshot()
    img.thumbnail((1568, 1568))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return ctx.brain.ask_image(buf.getvalue(), "This is my screen. " + m.string + ". Answer briefly.")


@skill(r"\b(?:what do you see|look through (?:the )?camera|what(?:'s| is) in front of me|use (?:the )?camera)\b")
def camera(m, ctx):
    import cv2
    cap = cv2.VideoCapture(0)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return "I couldn't access the camera."
    ok, png = cv2.imencode(".png", frame)
    return ctx.brain.ask_image(png.tobytes(), "This is a webcam frame. Describe what you see briefly.")
