"""
Seed the vehicles table with 200 realistic cars (40 per category).

Usage (from project root, with venv active):
    python -m scripts.seed_vehicles

Safe to re-run — skips plates that already exist.
"""

import asyncio
from decimal import Decimal
from itertools import cycle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.vehicle import FuelType, Vehicle, VehicleCategory, VehicleStatus

# ---------------------------------------------------------------------------
# Unsplash image pools per category
# ---------------------------------------------------------------------------
_U = "https://images.unsplash.com/photo-{}?auto=format&fit=crop&w=800&q=80"

_IMGS = {
    "economy": cycle([_U.format(i) for i in [
        "1541443131876-44b03de101c5",
        "1574712836617-a2b24c8bf8d5",
        "1533473359331-0135ef1b58bf",
        "1503376780353-7e6692767b70",
        "1612826580668-c428e3a61789",
        "1581650107595-d51e2fba60aa",
        "1590362891991-f776e747a588",
        "1609521263047-f8f205293f24",
    ]]),
    "standard": cycle([_U.format(i) for i in [
        "1583121274602-3e2820c69888",
        "1549399542-7a000b2f87ee",
        "1494976388531-d1058494cdd8",
        "1621012891819-c98651c8e3d8",
        "1568605117036-5c5a1b3a23c3",
        "1503376780353-7e6692767b70",
        "1533473359331-0135ef1b58bf",
        "1583121274602-3e2820c69888",
    ]]),
    "premium": cycle([_U.format(i) for i in [
        "1555215695-3004980ad54e",
        "1552519507-da3b142b5f44",
        "1580274455191-1c62238fa1c6",
        "1543465077-db45d34b88a5",
        "1506015391300-4baba3244b87",
        "1567818735868-e71b99932e29",
        "1494976388531-d1058494cdd8",
        "1621012891819-c98651c8e3d8",
    ]]),
    "suv": cycle([_U.format(i) for i in [
        "1614162692292-7ac56d7f7f1e",
        "1592150550880-e5e3aa40e45c",
        "1573950940509-d924ee3fd345",
        "1619767886558-efdc259cde1a",
        "1568605117036-5c5a1b3a23c3",
        "1583121274602-3e2820c69888",
        "1555215695-3004980ad54e",
        "1580274455191-1c62238fa1c6",
    ]]),
    "van": cycle([_U.format(i) for i in [
        "1570733577-6d7ef7b48c0e",
        "1504215680197-fc79cf5e601e",
        "1609521263047-f8f205293f24",
        "1574712836617-a2b24c8bf8d5",
        "1590362891991-f776e747a588",
        "1541443131876-44b03de101c5",
        "1503376780353-7e6692767b70",
        "1533473359331-0135ef1b58bf",
    ]]),
}

# ---------------------------------------------------------------------------
# Car data — (make, model, year, fuel, seats, daily_rate_inr)
# Plates are auto-generated as KA-01-{PREFIX}-{NNNN}
# ---------------------------------------------------------------------------

ECONOMY: list[tuple] = [
    ("Maruti Suzuki", "Alto K10",          2023, "petrol",  5,  700),
    ("Maruti Suzuki", "Alto 800",          2022, "petrol",  5,  600),
    ("Maruti Suzuki", "WagonR 1.0",        2023, "petrol",  5,  800),
    ("Maruti Suzuki", "WagonR CNG",        2023, "petrol",  5,  750),
    ("Maruti Suzuki", "S-Presso",          2023, "petrol",  5,  700),
    ("Maruti Suzuki", "Celerio",           2023, "petrol",  5,  800),
    ("Maruti Suzuki", "Celerio CNG",       2022, "petrol",  5,  750),
    ("Maruti Suzuki", "Ignis",             2022, "petrol",  5,  850),
    ("Maruti Suzuki", "Swift LXi",         2023, "petrol",  5,  850),
    ("Maruti Suzuki", "Eeco 5-Seat",       2023, "petrol",  5,  800),
    ("Hyundai",       "Santro",            2022, "petrol",  5,  800),
    ("Hyundai",       "Grand i10",         2022, "petrol",  5,  800),
    ("Hyundai",       "Grand i10 NIOS",    2023, "petrol",  5,  850),
    ("Hyundai",       "i10 Era",           2021, "petrol",  5,  700),
    ("Tata",          "Tiago XE",          2023, "petrol",  5,  800),
    ("Tata",          "Tiago CNG",         2023, "petrol",  5,  750),
    ("Tata",          "Punch Adventure",   2023, "petrol",  5,  900),
    ("Tata",          "Nano GenX",         2017, "petrol",  4,  500),
    ("Renault",       "Kwid RXE",          2022, "petrol",  5,  700),
    ("Renault",       "Kwid 1.0 RXT",      2023, "petrol",  5,  750),
    ("Renault",       "Triber RXE",        2022, "petrol",  7,  850),
    ("Datsun",        "Redi-GO T",         2021, "petrol",  5,  650),
    ("Datsun",        "GO T",              2021, "petrol",  5,  700),
    ("Toyota",        "Glanza E",          2022, "petrol",  5,  850),
    ("Honda",         "Jazz V",            2020, "petrol",  5,  900),
    ("Honda",         "Brio",              2019, "petrol",  5,  700),
    ("Volkswagen",    "Polo Trendline",    2020, "petrol",  5,  900),
    ("Nissan",        "Magnite XE",        2023, "petrol",  5,  950),
    ("Nissan",        "Micra XV",          2019, "petrol",  5,  750),
    ("Ford",          "Figo Ambiente",     2019, "petrol",  5,  700),
    ("Ford",          "Freestyle Ambiente",2019, "petrol",  5,  750),
    ("Chevrolet",     "Beat LS",           2018, "petrol",  5,  650),
    ("Chevrolet",     "Spark LS",          2017, "petrol",  5,  600),
    ("Fiat",          "Punto Pure",        2017, "petrol",  5,  600),
    ("Maruti Suzuki", "A-Star",            2015, "petrol",  5,  600),
    ("Maruti Suzuki", "Estilo",            2015, "petrol",  5,  600),
    ("Maruti Suzuki", "Zen Estilo",        2014, "petrol",  5,  550),
    ("Tata",          "Indica Vista",      2015, "petrol",  5,  600),
    ("Hyundai",       "Eon Era+",          2018, "petrol",  5,  600),
    ("Maruti Suzuki", "Dzire LXi",         2021, "petrol",  5,  900),
]

STANDARD: list[tuple] = [
    ("Maruti Suzuki", "Dzire ZXi",         2023, "petrol",  5, 1100),
    ("Maruti Suzuki", "Dzire ZDi",         2023, "diesel",  5, 1150),
    ("Maruti Suzuki", "Baleno Alpha",      2023, "petrol",  5, 1200),
    ("Maruti Suzuki", "Baleno Delta CNG",  2023, "petrol",  5, 1100),
    ("Maruti Suzuki", "Swift ZXi",         2023, "petrol",  5, 1100),
    ("Maruti Suzuki", "Ciaz Alpha",        2022, "petrol",  5, 1300),
    ("Maruti Suzuki", "Ciaz Delta Diesel", 2022, "diesel",  5, 1300),
    ("Maruti Suzuki", "XL6 Zeta",         2023, "petrol",  6, 1500),
    ("Honda",         "Amaze VX CVT",      2023, "petrol",  5, 1100),
    ("Honda",         "City V",            2022, "petrol",  5, 1300),
    ("Honda",         "City 4th Gen",      2021, "petrol",  5, 1200),
    ("Honda",         "WR-V V",            2021, "petrol",  5, 1200),
    ("Honda",         "Jazz ZX",           2020, "petrol",  5, 1200),
    ("Hyundai",       "i20 Asta",          2023, "petrol",  5, 1200),
    ("Hyundai",       "i20 Sportz",        2023, "petrol",  5, 1100),
    ("Hyundai",       "Verna SX",          2023, "petrol",  5, 1400),
    ("Hyundai",       "Elantra Elite",     2019, "petrol",  5, 1400),
    ("Hyundai",       "Xcent S",           2018, "petrol",  5, 1000),
    ("Toyota",        "Glanza V",          2023, "petrol",  5, 1100),
    ("Toyota",        "Yaris J",           2019, "petrol",  5, 1200),
    ("Toyota",        "Etios VX",          2019, "petrol",  5, 1000),
    ("Toyota",        "Etios Liva VX",     2018, "petrol",  5,  950),
    ("Tata",          "Tigor XZ+",         2023, "petrol",  5, 1000),
    ("Tata",          "Altroz XZ+",        2023, "petrol",  5, 1100),
    ("Tata",          "Altroz DCA",        2023, "petrol",  5, 1200),
    ("Volkswagen",    "Polo GT TSI",       2021, "petrol",  5, 1200),
    ("Volkswagen",    "Vento Highline",    2021, "petrol",  5, 1300),
    ("Volkswagen",    "Virtus Topline",    2023, "petrol",  5, 1400),
    ("Skoda",         "Slavia Ambition",   2023, "petrol",  5, 1400),
    ("Skoda",         "Rapid Rider+",      2021, "petrol",  5, 1300),
    ("Skoda",         "Fabia Ambition",    2020, "petrol",  5, 1200),
    ("Skoda",         "Kushaq Active",     2022, "petrol",  5, 1500),
    ("Nissan",        "Sunny XV Premium",  2020, "petrol",  5, 1100),
    ("Nissan",        "Magnite XV Turbo",  2023, "petrol",  5, 1100),
    ("Renault",       "Duster RXL",        2019, "petrol",  5, 1300),
    ("Renault",       "Kiger RXL",         2023, "petrol",  5, 1100),
    ("Citroen",       "C3 Feel",           2023, "petrol",  5, 1100),
    ("Ford",          "Aspire Titanium",   2018, "petrol",  5, 1100),
    ("Fiat",          "Linea T-Jet",       2016, "petrol",  5, 1000),
    ("Hyundai",       "i20 Active SX",     2019, "petrol",  5, 1100),
]

PREMIUM: list[tuple] = [
    ("Honda",         "Civic ZX CVT",          2020, "petrol",  5,  2000),
    ("Skoda",         "Octavia L&K",           2022, "petrol",  5,  2200),
    ("Volkswagen",    "Virtus GT DSG",         2023, "petrol",  5,  2000),
    ("Volkswagen",    "Passat Highline",       2019, "petrol",  5,  2200),
    ("Toyota",        "Camry Hybrid",          2023, "hybrid",  5,  3500),
    ("Toyota",        "Fortuner Legender",     2023, "diesel",  7,  4000),
    ("Jeep",          "Compass Limited+",      2022, "petrol",  5,  2500),
    ("Jeep",          "Meridian Limited+",     2022, "diesel",  7,  3500),
    ("BMW",           "3 Series 320d",         2022, "petrol",  5,  5000),
    ("BMW",           "3 Series 330i M Sport", 2023, "petrol",  5,  5500),
    ("BMW",           "5 Series 520d",         2022, "diesel",  5,  6500),
    ("BMW",           "5 Series 530i M Sport", 2022, "petrol",  5,  7000),
    ("BMW",           "7 Series 730Ld",        2022, "diesel",  5,  9000),
    ("BMW",           "X1 sDrive18i",          2023, "petrol",  5,  4500),
    ("BMW",           "X3 xDrive20d",          2022, "diesel",  5,  6000),
    ("BMW",           "M3 Competition",        2022, "petrol",  5,  8000),
    ("Mercedes-Benz", "C 200 AMG Line",        2022, "petrol",  5,  6000),
    ("Mercedes-Benz", "C 220d AMG Line",       2022, "diesel",  5,  6500),
    ("Mercedes-Benz", "E 220d",                2022, "diesel",  5,  7500),
    ("Mercedes-Benz", "E 450 4MATIC",          2022, "petrol",  5,  8500),
    ("Mercedes-Benz", "S 350d 4MATIC",         2022, "diesel",  5, 12000),
    ("Mercedes-Benz", "GLA 200",               2022, "petrol",  5,  5500),
    ("Mercedes-Benz", "GLC 300 4MATIC",        2022, "petrol",  5,  7000),
    ("Audi",          "A4 Premium Plus",       2022, "petrol",  5,  5500),
    ("Audi",          "A6 Technology Pack",    2022, "petrol",  5,  7000),
    ("Audi",          "A8 L",                  2022, "petrol",  5, 10000),
    ("Audi",          "Q3 Premium Plus",       2023, "petrol",  5,  5000),
    ("Audi",          "Q5 Technology Pack",    2022, "petrol",  5,  7500),
    ("Volvo",         "S60 B5",                2022, "petrol",  5,  5000),
    ("Volvo",         "S90 B6",                2022, "petrol",  5,  7000),
    ("Volvo",         "XC40 B4",               2022, "petrol",  5,  5500),
    ("Jaguar",        "XE SE",                 2021, "petrol",  5,  5000),
    ("Jaguar",        "XF Portfolio",          2021, "petrol",  5,  6000),
    ("Lexus",         "ES 300h",               2022, "hybrid",  5,  6000),
    ("Lexus",         "NX 350h",               2022, "hybrid",  5,  7000),
    ("Genesis",       "G80 Standard",          2022, "petrol",  5,  5000),
    ("Kia",           "EV6 GT-Line",           2023, "electric",5,  4500),
    ("Porsche",       "Macan S",               2022, "petrol",  5, 10000),
    ("Porsche",       "Cayenne Coupé",         2022, "petrol",  5, 15000),
    ("Maserati",      "Ghibli GT",             2021, "petrol",  5, 10000),
]

SUV: list[tuple] = [
    ("Tata",          "Nexon XZ+ Dark",        2023, "petrol",  5,  1500),
    ("Tata",          "Nexon EV Max",          2023, "electric",5,  2000),
    ("Tata",          "Harrier XZA+",          2023, "diesel",  5,  2200),
    ("Tata",          "Safari Gold",           2023, "diesel",  7,  2500),
    ("Tata",          "Punch Adventure",       2023, "petrol",  5,  1400),
    ("Tata",          "Curvv EV",              2024, "electric",5,  2200),
    ("Hyundai",       "Creta SX(O)",           2023, "petrol",  5,  1800),
    ("Hyundai",       "Venue N Line",          2023, "petrol",  5,  1600),
    ("Hyundai",       "Tucson Signature",      2022, "petrol",  5,  2800),
    ("Hyundai",       "Ioniq 5 Platinum",      2023, "electric",5,  4000),
    ("Kia",           "Seltos HTX+",           2023, "petrol",  5,  1900),
    ("Kia",           "Sonet HTX+",            2023, "petrol",  5,  1500),
    ("Kia",           "Carnival Limousine",    2022, "diesel",  7,  3500),
    ("Kia",           "EV9 GT-Line",           2024, "electric",7,  5000),
    ("Mahindra",      "Scorpio-N Z8L",         2023, "diesel",  7,  2200),
    ("Mahindra",      "XUV700 AX7L AWD",       2023, "diesel",  7,  3000),
    ("Mahindra",      "Thar LX 4WD",           2023, "diesel",  4,  2000),
    ("Mahindra",      "XUV300 W8(O)",          2023, "petrol",  5,  1700),
    ("Mahindra",      "XUV400 EV Pro",         2023, "electric",5,  2200),
    ("Mahindra",      "BE 6e",                 2024, "electric",5,  2500),
    ("Toyota",        "Fortuner 4×4 AT",       2022, "diesel",  7,  4000),
    ("Toyota",        "RAV4 Hybrid",           2023, "hybrid",  5,  4500),
    ("Toyota",        "Urban Cruiser Hyryder", 2023, "hybrid",  5,  2000),
    ("Toyota",        "Land Cruiser 300",      2022, "diesel",  7, 12000),
    ("Honda",         "WR-V ZX",               2022, "petrol",  5,  1500),
    ("MG",            "Hector Sharp+",         2023, "petrol",  5,  2000),
    ("MG",            "ZS EV Exclusive",       2023, "electric",5,  2200),
    ("MG",            "Gloster Sharp 4WD",     2023, "diesel",  7,  3500),
    ("MG",            "Astor Sharp",           2023, "petrol",  5,  1900),
    ("Jeep",          "Compass Night Eagle",   2022, "diesel",  5,  2500),
    ("Volkswagen",    "Taigun GT DSG",         2023, "petrol",  5,  2000),
    ("Skoda",         "Kushaq Monte Carlo",    2023, "petrol",  5,  2000),
    ("BMW",           "X5 xDrive40i",          2022, "petrol",  5,  8000),
    ("Mercedes-Benz", "GLC 300 4MATIC",        2022, "petrol",  5,  7000),
    ("Audi",          "Q5 55 TFSI quattro",    2022, "petrol",  5,  7500),
    ("Volvo",         "XC60 B5",               2022, "petrol",  5,  6000),
    ("Land Rover",    "Discovery Sport SE",    2022, "diesel",  5,  8000),
    ("Land Rover",    "Defender 110 SE",       2022, "diesel",  5, 15000),
    ("Nissan",        "Magnite Turbo CVT",     2023, "petrol",  5,  1200),
    ("Renault",       "Duster AWD Diesel",     2019, "diesel",  5,  1500),
]

VAN: list[tuple] = [
    ("Toyota",        "Innova Crysta 2.7 VX",  2022, "petrol",  7,  3000),
    ("Toyota",        "Innova Crysta 2.4 GX",  2022, "diesel",  7,  2500),
    ("Toyota",        "Innova Crysta 2.4 ZX",  2022, "diesel",  7,  3200),
    ("Toyota",        "Innova HyCross ZX(O)",  2023, "hybrid",  7,  4000),
    ("Toyota",        "Innova HyCross VX",     2023, "hybrid",  7,  3200),
    ("Toyota",        "Innova HyCross GX+",    2023, "hybrid",  7,  2800),
    ("Toyota",        "Hiace Commuter",        2022, "diesel", 14,  4500),
    ("Toyota",        "Alphard Executive",     2022, "hybrid",  7,  8000),
    ("Maruti Suzuki", "Ertiga VXi",            2023, "petrol",  7,  1800),
    ("Maruti Suzuki", "Ertiga ZXi+",           2023, "petrol",  7,  2000),
    ("Maruti Suzuki", "Ertiga CNG VXi",        2023, "petrol",  7,  1750),
    ("Maruti Suzuki", "XL6 Alpha",             2023, "petrol",  6,  2200),
    ("Maruti Suzuki", "XL6 Zeta",             2023, "petrol",  6,  2000),
    ("Maruti Suzuki", "Eeco 7-Seat",           2023, "petrol",  7,  1300),
    ("Maruti Suzuki", "Omni",                  2019, "petrol",  8,  1000),
    ("Kia",           "Carens Luxury+ DCT",    2023, "diesel",  7,  2500),
    ("Kia",           "Carens Premium",        2023, "petrol",  6,  2200),
    ("Kia",           "Carens Technology",     2023, "diesel",  6,  2000),
    ("Kia",           "Carnival Prestige",     2022, "diesel",  7,  3500),
    ("Mahindra",      "Bolero B6",             2022, "diesel",  7,  1600),
    ("Mahindra",      "Bolero Neo N10(O)",     2023, "diesel",  7,  1800),
    ("Mahindra",      "Marazzo M8",            2022, "diesel",  8,  2200),
    ("Mahindra",      "Marazzo M4",            2022, "diesel",  7,  2000),
    ("Mahindra",      "Scorpio Classic",       2022, "diesel",  7,  2000),
    ("Force",         "Gurkha 5-Door",         2023, "diesel",  4,  2500),
    ("Force",         "Traveller 3350",        2022, "diesel", 12,  3500),
    ("Tata",          "Winger Deluxe",         2022, "diesel", 13,  3500),
    ("Tata",          "Venture LX",            2021, "diesel",  7,  2000),
    ("Tata",          "Sumo Gold GX",          2020, "diesel",  7,  1500),
    ("Tata",          "Magic Express",         2022, "diesel",  9,  2200),
    ("Renault",       "Triber RXZ AMT",        2023, "petrol",  7,  1500),
    ("Renault",       "Lodgy World Edition",   2016, "diesel",  7,  1300),
    ("Honda",         "Mobilio VX CVT",        2016, "petrol",  7,  1400),
    ("Nissan",        "Evalia XV",             2015, "diesel",  7,  1200),
    ("Chevrolet",     "Enjoy LT",              2014, "diesel",  7,  1200),
    ("Mercedes-Benz", "V 220d",                2021, "diesel",  8,  5000),
    ("Volkswagen",    "Caravelle 2.0 TDI",     2021, "diesel",  9,  5000),
    ("Mahindra",      "e-Supro Cargo",         2022, "electric", 5,  1400),
    ("Honda",         "BR-V V CVT",            2016, "petrol",  7,  1400),
    ("Maruti Suzuki", "Versa DX",              2015, "petrol",  8,  1000),
]

# ---------------------------------------------------------------------------
# Plate prefix per category
# ---------------------------------------------------------------------------
_PREFIX = {
    "economy":  "EC",
    "standard": "ST",
    "premium":  "PR",
    "suv":      "SV",
    "van":      "VN",
}

CATALOGUE: dict[str, list[tuple]] = {
    "economy":  ECONOMY,
    "standard": STANDARD,
    "premium":  PREMIUM,
    "suv":      SUV,
    "van":      VAN,
}


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        existing_plates = {
            row[0] for row in (await db.execute(select(Vehicle.license_plate))).all()
        }

        new_vehicles: list[Vehicle] = []

        for cat, cars in CATALOGUE.items():
            prefix = _PREFIX[cat]
            img_iter = _IMGS[cat]

            for idx, (make, model, year, fuel, seats, rate) in enumerate(cars, start=1):
                plate = f"KA-01-{prefix}-{idx:04d}"
                if plate in existing_plates:
                    continue

                new_vehicles.append(Vehicle(
                    make=make,
                    model=model,
                    year=year,
                    license_plate=plate,
                    category=VehicleCategory(cat),
                    daily_rate=Decimal(str(rate)),
                    fuel_type=FuelType(fuel),
                    seats=seats,
                    image_url=next(img_iter),
                    status=VehicleStatus.available,
                ))

        if not new_vehicles:
            print("Nothing to insert — all plates already exist.")
        else:
            db.add_all(new_vehicles)
            await db.commit()
            print(f"Inserted {len(new_vehicles)} vehicles.")
            for cat in CATALOGUE:
                count = sum(1 for v in new_vehicles if v.category.value == cat)
                print(f"  {cat:10s}: {count}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
