import subprocess 
import os

pngFiles = os.listdir(".")

for f in pngFiles:
    if f.endswith(".png"):
        print(f)
        outfile = f.replace(".png", ".gif")
        cmd = "convert -scale 10% " + f + " " + outfile
        cmds = cmd.split()
        subprocess.run(cmds)
        
