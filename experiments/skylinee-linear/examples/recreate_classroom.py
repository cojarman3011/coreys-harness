"""Rebuild original seeded 30-point teaching dataset (not real-world observations)."""
import csv

import numpy as np
rs=np.random.RandomState(10)
x=5*rs.rand(30);y=3*x-2+rs.randn(30)
with open("classroom_30.csv","w",newline="") as f:
    writer=csv.writer(f);writer.writerow(["x","y"]);writer.writerows(zip(x,y))
beta=float(np.dot(x,y)/np.dot(x,x))
print(f"Original full-data, zero-intercept slope: {beta:.8f}; x=6: {beta*6:.8f}")
print("Note: Skylinee train uses a holdout, so its new fitted slope differs.")
