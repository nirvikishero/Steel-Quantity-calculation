import math
from itertools import combinations_with_replacement

steel_dia = [8, 10, 12, 16, 20, 25, 28, 32]
steel_area = {d: (math.pi / 4) * d**2 for d in steel_dia}

required_area = float(input("Enter required steel area (mm^2): "))

max_bars = 8
solutions = []

for r in range(2, max_bars + 1):  # minimum 2 bars
    for combo in combinations_with_replacement(steel_dia, r):

        total_area = sum(steel_area[d] for d in combo)

        if total_area >= required_area:
            excess = total_area - required_area

            # Count bars
            result = {}
            for d in combo:
                result[d] = result.get(d, 0) + 1

            solutions.append((r, excess, result, total_area))

# 🔥 Sort solutions:
# 1. Minimum bars
# 2. Minimum excess
solutions.sort(key=lambda x: (x[0], x[1]))

# Display
print(f"\nFound {len(solutions)} possible solutions:\n")

for i, (bars, excess, result, total) in enumerate(solutions[:20], 1):  
    # show top 20 only (avoid spam)
    print(f"Option {i}:")
    
    for dia, count in sorted(result.items()):
        print(f"  {count} bar(s) of {dia} mm")
    
    print(f"  Total area = {total:.2f} mm²")
    print(f"  Excess = {excess:.2f} mm²\n")