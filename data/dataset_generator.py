# no. 2
import json
import random
import os

SITES = [
    "Naharkatia Flow Station",
    "Digboi Oilfield - Well #42",
    "Moran Central Tank Farm",
    "Jorajan Drilling Rig-04",
    "Duliamen Gas Compression Plant",
    "Makum Crude Terminal",
    "Kumchai Well Site #12",
    "Shalmari Pipeline Junction",
    "Baghjan Production Unit",
    "Tinsukia Depot & Haulage"
]

ACTIVITIES = [
    "Wireline servicing",
    "Pipe handling & tripping",
    "Tank & vessel cleaning",
    "Flange bolt torqueing & valve replacement",
    "Wellhead maintenance",
    "Derrick maintenance & inspection",
    "Scaffold erection & dismantling",
    "Hot work & welding on hydrocarbon line",
    "Electrical sub-station maintenance",
    "Crude haulage & tanker driving",
    "Excavation & trenching near flowline",
    "Workover operations"
]

REPORT_TYPES = ["UA", "UC", "Near-Miss", "Incident"]

BARRIER_FAILURE_CATEGORIES = [
    "LOTO / Energy Isolation Bypassed",
    "Permit to Work (PTW) Non-Compliance",
    "PPE Not Worn / Defective",
    "Gas Test Not Performed",
    "Fall Protection / Harness Unhooked",
    "Defective Lifting Gear / Unrated Sling",
    "Inadequate Guarding / Machine Guard Removed",
    "Line of Fire / Standing Under Suspended Load",
    "Unauthorized Modification / MOC Ignored",
    "Journey Management & Speeding Violation"
]

LSR_RULES = [
    "Energy Isolation",
    "Hot Work",
    "Confined Space",
    "Line of Fire",
    "Working at Height",
    "Driving",
    "Lifting Operations",
    "Management of Change",
    "Safe Mechanical Lifting",
    "Permit to Work",
    "Bypassing Safety Controls"
]

SEED_NARRATIVES = [
    # --- SIF PRECURSORS (High Energy + Control Absent/Not Followed) ---
    {
        "narrative": "During wellhead maintenance at Naharkatia Flow Station, technician initiated valve dismantling without verifying LOTO or bleeding pressure from the Christmas tree manifold. Pressure gauge showed 450 PSI trapped.",
        "energy_source": "Pressure",
        "control_status": "absent",
        "sif_potential": True,
        "lsr": ["Energy Isolation", "Permit to Work"],
        "barrier_failure": "LOTO / Energy Isolation Bypassed",
        "filer_severity": "Low",
        "report_type": "Near-Miss",
        "site": "Naharkatia Flow Station",
        "activity": "Wellhead maintenance"
    },
    {
        "narrative": "Contract welder observed performing hot work on active hydrocarbon line near pump house without conducting gas testing or obtaining a valid PTW. Flammable vapors present in area.",
        "energy_source": "Chemical/Thermal",
        "control_status": "not_followed",
        "sif_potential": True,
        "lsr": ["Hot Work", "Permit to Work"],
        "barrier_failure": "Gas Test Not Performed",
        "filer_severity": "Medium",
        "report_type": "UA",
        "site": "Digboi Oilfield - Well #42",
        "activity": "Hot work & welding on hydrocarbon line"
    },
    {
        "narrative": "Roustabout climbed 18 meters up monkey board at Jorajan Drilling Rig-04 to clear stuck traveling block without hooking fall arrest harness. Guard rails were damaged.",
        "energy_source": "Gravity",
        "control_status": "not_followed",
        "sif_potential": True,
        "lsr": ["Working at Height"],
        "barrier_failure": "Fall Protection / Harness Unhooked",
        "filer_severity": "Low",
        "report_type": "UA",
        "site": "Jorajan Drilling Rig-04",
        "activity": "Derrick maintenance & inspection"
    },
    {
        "narrative": "Helper stood directly underneath 4-ton drill pipe bundle suspended from crane hook while sling was frayed and uncertified. Tag line was not used.",
        "energy_source": "Gravity",
        "control_status": "absent",
        "sif_potential": True,
        "lsr": ["Lifting Operations", "Line of Fire", "Safe Mechanical Lifting"],
        "barrier_failure": "Line of Fire / Standing Under Suspended Load",
        "filer_severity": "Low",
        "report_type": "Near-Miss",
        "site": "Jorajan Drilling Rig-04",
        "activity": "Pipe handling & tripping"
    },
    {
        "narrative": "Two cleaners entered crude storage tank T-102 at Moran CTF without continuous gas monitoring or standby attendant positioned outside. Oxygen level was unverified.",
        "energy_source": "Chemical/Thermal",
        "control_status": "absent",
        "sif_potential": True,
        "lsr": ["Confined Space", "Permit to Work"],
        "barrier_failure": "Permit to Work (PTW) Non-Compliance",
        "filer_severity": "Medium",
        "report_type": "UA",
        "site": "Moran Central Tank Farm",
        "activity": "Tank & vessel cleaning"
    },
    {
        "narrative": "Technician opened electrical panel 415V MCC at Duliamen Gas Plant with live busbars exposed and interlocking mechanism bypassed using screwdriver.",
        "energy_source": "Electrical",
        "control_status": "not_followed",
        "sif_potential": True,
        "lsr": ["Energy Isolation", "Bypassing Safety Controls"],
        "barrier_failure": "Inadequate Guarding / Machine Guard Removed",
        "filer_severity": "Medium",
        "report_type": "UA",
        "site": "Duliamen Gas Compression Plant",
        "activity": "Electrical sub-station maintenance"
    },
    {
        "narrative": "Crude oil tanker driver observed traveling at 75 km/h on narrow single-lane access road in wet conditions near Tinsukia Depot, bypassing journey plan and using mobile phone while driving.",
        "energy_source": "Motion/Vehicle",
        "control_status": "not_followed",
        "sif_potential": True,
        "lsr": ["Driving"],
        "barrier_failure": "Journey Management & Speeding Violation",
        "filer_severity": "Low",
        "report_type": "UA",
        "site": "Tinsukia Depot & Haulage",
        "activity": "Crude haulage & tanker driving"
    },
    {
        "narrative": "Field engineer installed temporary bypass hose on 600 PSI condensate header without Management of Change (MOC) review or pressure rating check.",
        "energy_source": "Pressure",
        "control_status": "not_followed",
        "sif_potential": True,
        "lsr": ["Management of Change"],
        "barrier_failure": "Unauthorized Modification / MOC Ignored",
        "filer_severity": "Low",
        "report_type": "UC",
        "site": "Baghjan Production Unit",
        "activity": "Flange bolt torqueing & valve replacement"
    },
    {
        "narrative": "Operator removed safety guard from high-speed mud pump drive belt while equipment was running to apply belt dressing manually.",
        "energy_source": "Mechanical",
        "control_status": "absent",
        "sif_potential": True,
        "lsr": ["Bypassing Safety Controls", "Line of Fire"],
        "barrier_failure": "Inadequate Guarding / Machine Guard Removed",
        "filer_severity": "Low",
        "report_type": "UA",
        "site": "Jorajan Drilling Rig-04",
        "activity": "Workover operations"
    },
    {
        "narrative": "Excavator digging trench near live high-pressure gas pipeline at Makum without hand digging or utility mapping. Operator bypassed PTW clearance depth limit.",
        "energy_source": "Pressure",
        "control_status": "not_followed",
        "sif_potential": True,
        "lsr": ["Permit to Work", "Line of Fire"],
        "barrier_failure": "Permit to Work (PTW) Non-Compliance",
        "filer_severity": "Medium",
        "report_type": "Near-Miss",
        "site": "Makum Crude Terminal",
        "activity": "Excavation & trenching near flowline"
    },

    # --- NON-SIF PRECURSORS / SAFE HIGH ENERGY (High Energy BUT Controls Present & Followed) ---
    {
        "narrative": "Rig crew performed heavy lift of 12-ton blowout preventer (BOP) at Rig-04. Certified crane used, lift plan verified, LOTO applied, exclusion zone barriered with taglines attached. Zero unauthorized entry.",
        "energy_source": "Gravity",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": ["Lifting Operations", "Safe Mechanical Lifting"],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UA",
        "site": "Jorajan Drilling Rig-04",
        "activity": "Pipe handling & tripping"
    },
    {
        "narrative": "Contractor carried out grinding work on pipeline support bracket at Shalmari. PTW active, 10-meter gas check completed showing 0% LEL, fire watch posted with dual extinguisher, face shield worn.",
        "energy_source": "Chemical/Thermal",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": ["Hot Work", "Permit to Work"],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UA",
        "site": "Shalmari Pipeline Junction",
        "activity": "Hot work & welding on hydrocarbon line"
    },
    {
        "narrative": "Scaffolder erected 12m work platform at Kumchai Well Site. Dual lanyard safety harness hooked to certified anchor point, hard hat secured, toe boards installed as per HSE guidelines.",
        "energy_source": "Gravity",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": ["Working at Height"],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UA",
        "site": "Kumchai Well Site #12",
        "activity": "Scaffold erection & dismantling"
    },
    {
        "narrative": "Tanker driver completed journey with full IVMS compliance, seatbelt worn, speed within limits, journey plan followed. Vehicle inspection checklist completed before departure.",
        "energy_source": "Motion/Vehicle",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": ["Driving"],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UA",
        "site": "Tinsukia Depot & Haulage",
        "activity": "Crude haulage & tanker driving"
    },
    {
        "narrative": "Electrical maintenance on 415V switchgear completed at Duliamen. Full LOTO applied, verified dead with multimeter, earthing applied, PTW signed off, arc flash PPE worn throughout.",
        "energy_source": "Electrical",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": ["Energy Isolation", "Permit to Work"],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UA",
        "site": "Duliamen Gas Compression Plant",
        "activity": "Electrical sub-station maintenance"
    },
    {
        "narrative": "Confined space entry into vessel V-201 at Moran CTF completed safely. Gas test showed 20.9% O2, 0 ppm H2S, 0% LEL. Standby attendant posted, PTW active, rescue plan reviewed.",
        "energy_source": "Chemical/Thermal",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": ["Confined Space", "Permit to Work"],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UA",
        "site": "Moran Central Tank Farm",
        "activity": "Tank & vessel cleaning"
    },

    # --- NON-SIF PRECURSORS (Low Energy / Minor Routine Observations) ---
    {
        "narrative": "Housekeeping observation: Paper waste and empty plastic tea cups noticed near office entrance steps at Naharkatia admin building. Slips/trips hazard.",
        "energy_source": "None",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": [],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UC",
        "site": "Naharkatia Flow Station",
        "activity": "Wellhead maintenance"
    },
    {
        "narrative": "Ergonomics report: Control room operator reported mild back discomfort due to non-adjustable office chair in Moran monitoring cabin.",
        "energy_source": "None",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": [],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UC",
        "site": "Moran Central Tank Farm",
        "activity": "Wellhead maintenance"
    },
    {
        "narrative": "Safety boots shoelace found untied during safety walk near store room gate. Worker advised to tie lace immediately.",
        "energy_source": "None",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": [],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UA",
        "site": "Digboi Oilfield - Well #42",
        "activity": "Wireline servicing"
    },
    {
        "narrative": "Minor environmental observation: Small oil sheen noticed on rainwater puddle near diesel generator set at Kumchai. Drip tray was overflowing. Maintenance team alerted.",
        "energy_source": "None",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": [],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UC",
        "site": "Kumchai Well Site #12",
        "activity": "Wellhead maintenance"
    },
    {
        "narrative": "Routine toolbox talk conducted before scaffold work at Baghjan. All crew confirmed understanding of risk assessment and emergency muster point.",
        "energy_source": "None",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": [],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UA",
        "site": "Baghjan Production Unit",
        "activity": "Scaffold erection & dismantling"
    },
    {
        "narrative": "First aid case: Worker sustained minor scratch on forearm while handling clean pipe fittings in store. Band-aid applied on site by first aider.",
        "energy_source": "None",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": [],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "Incident",
        "site": "Shalmari Pipeline Junction",
        "activity": "Pipe handling & tripping"
    },
    {
        "narrative": "Noise level observation: Ambient noise near compressor house exceeded 85 dB during routine check. Workers confirmed wearing ear plugs. Signage verified in place.",
        "energy_source": "None",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": [],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UC",
        "site": "Duliamen Gas Compression Plant",
        "activity": "Wellhead maintenance"
    },
    {
        "narrative": "Traffic management: Temporary speed bump installed near new construction area at Makum. All drivers briefed during morning safety meeting.",
        "energy_source": "None",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": [],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UA",
        "site": "Makum Crude Terminal",
        "activity": "Crude haulage & tanker driving"
    },
    {
        "narrative": "Expired fire extinguisher discovered during monthly inspection at Tinsukia office block. Replaced immediately with serviced unit. Log updated.",
        "energy_source": "None",
        "control_status": "followed",
        "sif_potential": False,
        "lsr": [],
        "barrier_failure": "None",
        "filer_severity": "Low",
        "report_type": "UC",
        "site": "Tinsukia Depot & Haulage",
        "activity": "Wellhead maintenance"
    }
]

# Variations and code-mix templates to generate 250 records
CODE_MIX_CUES = [
    ("without permit", "bina PTW permit ke"),
    ("harness unhooked", "safety belt nahi lagaya gaya tha"),
    ("LOTO bypassed", "lockout tagout chhod diya gaya"),
    ("standing under load", "suspended pipe load ke neeche khada tha"),
    ("gas test missing", "gas testing missing tha"),
    ("speeding", "tez gaadi chala raha tha"),
    ("guard removed", "guard nikal diya gaya tha"),
    ("no helmet worn", "helmet nahi pehna tha"),
]

def generate_dataset(total_count=250):
    dataset = []
    
    # 1. First populate seed items
    for idx, item in enumerate(SEED_NARRATIVES):
        record = {
            "report_id": f"OIL-2026-{1000 + idx}",
            "timestamp": f"2026-{random.choice(['06','07','08'])}-{random.randint(1, 28):02d}T{random.randint(7, 19):02d}:{random.randint(10, 59):02d}:00Z",
            "site": item["site"],
            "activity": item["activity"],
            "report_type": item["report_type"],
            "narrative": item["narrative"],
            "filer_severity": item["filer_severity"],
            "ground_truth": {
                "energy_source": item["energy_source"],
                "control_status": item["control_status"],
                "sif_potential": item["sif_potential"],
                "life_saving_rules": item["lsr"],
                "barrier_failure_category": item["barrier_failure"]
            }
        }
        dataset.append(record)

    # 2. Expand variations to reach target count
    # Target distribution: ~35-40% SIF, ~60-65% non-SIF
    sif_templates = [
        # SIF Templates (Energy + Control Failure)
        {
            "template": "While carrying out {activity} at {site}, worker {control_issue} near {energy_object}. Trapped energy present.",
            "energy_source": "Pressure",
            "control_status": "absent",
            "sif_potential": True,
            "lsrs": ["Energy Isolation", "Permit to Work"],
            "barrier": "LOTO / Energy Isolation Bypassed",
            "control_issues": ["bypassed double block and bleed valve LOTO", "failed to bleed 600 PSI pressure before unbolting flange", "worked without isolation tag"],
            "energy_objects": ["high pressure manifold", "flowline separator", "discharge line header"]
        },
        {
            "template": "Contractor technician during {activity} at {site} was observed {control_issue} on {energy_object} height platform.",
            "energy_source": "Gravity",
            "control_status": "not_followed",
            "sif_potential": True,
            "lsrs": ["Working at Height"],
            "barrier": "Fall Protection / Harness Unhooked",
            "control_issues": ["working without lanyard hooked to lifeline", "standing on top rail of scaffold without harness", "bypassing fall arrest block"],
            "energy_objects": ["15m derrick platform", "20m crude tank roof", "scaffold structure"]
        },
        {
            "template": "During {activity} at {site}, crew performed welding {control_issue} near {energy_object}.",
            "energy_source": "Chemical/Thermal",
            "control_status": "not_followed",
            "sif_potential": True,
            "lsrs": ["Hot Work", "Permit to Work"],
            "barrier": "Gas Test Not Performed",
            "control_issues": ["without hot work permit", "without gas detector measurement", "bina PTW aur gas check ke"],
            "energy_objects": ["hydrocarbon drain valve", "gas compressor outlet", "crude sump pit"]
        },
        {
            "template": "Heavy lift during {activity} at {site}: rigger stood {control_issue} while hoisting {energy_object}.",
            "energy_source": "Gravity",
            "control_status": "absent",
            "sif_potential": True,
            "lsrs": ["Lifting Operations", "Line of Fire", "Safe Mechanical Lifting"],
            "barrier": "Line of Fire / Standing Under Suspended Load",
            "control_issues": ["directly underneath suspended load", "in pinch point area near crane boom", "without tagline guide"],
            "energy_objects": ["heavy 5-ton drill collar bundle", "BOP stack", "sub-structure section"]
        },
        {
            "template": "Driver operating tanker during {activity} at {site} was caught {control_issue} on access highway.",
            "energy_source": "Motion/Vehicle",
            "control_status": "not_followed",
            "sif_potential": True,
            "lsrs": ["Driving"],
            "barrier": "Journey Management & Speeding Violation",
            "control_issues": ["exceeding speed limit at 80km/h with mobile phone in hand", "overtaking on sharp turn without seatbelt", "driving fatigued past IVMS alert"],
            "energy_objects": ["40-KL crude transport tanker", "field utility vehicle", "heavy tractor trailer"]
        },
        {
            "template": "Maintenance team engaged in {activity} at {site} opened {energy_object} {control_issue}.",
            "energy_source": "Electrical",
            "control_status": "absent",
            "sif_potential": True,
            "lsrs": ["Energy Isolation"],
            "barrier": "Inadequate Guarding / Machine Guard Removed",
            "control_issues": ["without opening breaker LOTO switch", "with live 415V electrical busbar exposed", "bina arc flash PPE ke"],
            "energy_objects": ["main sub-station panel", "compressor motor junction box", "transformer cabinet"]
        },
        {
            "template": "During {activity} at {site}, workers entered confined space {control_issue} inside {energy_object}.",
            "energy_source": "Chemical/Thermal",
            "control_status": "absent",
            "sif_potential": True,
            "lsrs": ["Confined Space", "Permit to Work"],
            "barrier": "Permit to Work (PTW) Non-Compliance",
            "control_issues": ["without valid confined space permit", "without continuous gas monitoring", "without standby attendant at entry point"],
            "energy_objects": ["crude oil storage tank", "vessel V-103", "separator drum"]
        },
    ]

    safe_high_energy_templates = [
        # Safe High-Energy Templates (SIF Potential = False)
        {
            "template": "Planned {activity} completed at {site}. Full LOTO verified on {energy_object}, gas test recorded 0% LEL, PTW signed off by HSE officer.",
            "energy_source": "Pressure",
            "control_status": "followed",
            "sif_potential": False,
            "lsrs": ["Energy Isolation", "Permit to Work"],
            "barrier": "None",
            "control_issues": ["with double block LOTO and verified isolation"],
            "energy_objects": ["high pressure gas line", "condensate header", "production manifold"]
        },
        {
            "template": "Lifting operation for {activity} at {site} executed smoothly using certified rig gear, clear exclusion zone maintained, taglines in use on {energy_object}.",
            "energy_source": "Gravity",
            "control_status": "followed",
            "sif_potential": False,
            "lsrs": ["Lifting Operations", "Safe Mechanical Lifting"],
            "barrier": "None",
            "control_issues": ["with full lift plan compliance and certified slings"],
            "energy_objects": ["generator set", "pipe rack section", "mud pump assembly"]
        },
        {
            "template": "Hot work at {site} for {activity} completed. PTW active, gas check confirmed 0% LEL at {energy_object}, fire watch maintained with extinguisher on standby.",
            "energy_source": "Chemical/Thermal",
            "control_status": "followed",
            "sif_potential": False,
            "lsrs": ["Hot Work", "Permit to Work"],
            "barrier": "None",
            "control_issues": ["with valid hot work permit and gas clearance"],
            "energy_objects": ["pipeline weld joint", "pump casing repair point", "flange connection"]
        },
        {
            "template": "Height work during {activity} at {site}: scaffolder used dual lanyard system, certified anchor, and inspected harness on {energy_object}. Toe boards installed.",
            "energy_source": "Gravity",
            "control_status": "followed",
            "sif_potential": False,
            "lsrs": ["Working at Height"],
            "barrier": "None",
            "control_issues": ["with full fall protection per procedure"],
            "energy_objects": ["10m platform", "derrick crown section", "tank roof edge"]
        },
        {
            "template": "Driver completed journey from {site} for {activity} with IVMS compliance, journey plan followed, seatbelt worn, speed within limits on {energy_object} route.",
            "energy_source": "Motion/Vehicle",
            "control_status": "followed",
            "sif_potential": False,
            "lsrs": ["Driving"],
            "barrier": "None",
            "control_issues": ["with journey management plan fully complied"],
            "energy_objects": ["NH-37 highway section", "field access track", "depot approach road"]
        },
    ]

    low_energy_templates = [
        # Low Energy / Minor Observations (SIF Potential = False)
        {
            "template": "Minor safety observation during routine walk at {site}: {control_issue} near office entry.",
            "energy_source": "None",
            "control_status": "followed",
            "sif_potential": False,
            "lsrs": [],
            "barrier": "None",
            "control_issues": [
                "spilled water bottle on tile floor cleaned immediately",
                "loose cardboard box kept in walkway removed",
                "handrail dusty in admin building stairwell",
                "wet floor sign missing after mopping",
                "cable tray cover displaced near control room",
                "exit sign lighting dim, maintenance informed"
            ],
            "energy_objects": ["admin corridor"]
        },
        {
            "template": "PPE observation at {site} during {activity}: {control_issue}. Corrected on the spot.",
            "energy_source": "None",
            "control_status": "followed",
            "sif_potential": False,
            "lsrs": [],
            "barrier": "None",
            "control_issues": [
                "worker wearing worn-out safety gloves",
                "safety glasses found not anti-fog rated",
                "high visibility vest colour faded",
                "ear plugs not inserted properly",
                "safety shoes due for replacement"
            ],
            "energy_objects": ["work site"]
        },
        {
            "template": "Environmental observation at {site}: {control_issue}. Maintenance informed for corrective action.",
            "energy_source": "None",
            "control_status": "followed",
            "sif_potential": False,
            "lsrs": [],
            "barrier": "None",
            "control_issues": [
                "small oil drip from hydraulic line onto ground",
                "waste segregation bin overflowing at laydown area",
                "chemical drum label faded and unreadable",
                "drainage channel blocked with debris",
                "dust accumulation on battery room ventilation grille"
            ],
            "energy_objects": ["facility area"]
        },
        {
            "template": "Positive safety observation at {site}: {control_issue}. Commended during toolbox talk.",
            "energy_source": "None",
            "control_status": "followed",
            "sif_potential": False,
            "lsrs": [],
            "barrier": "None",
            "control_issues": [
                "crew voluntarily conducted pre-job risk assessment before routine task",
                "operator stopped work to clarify permit scope before proceeding",
                "foreman ensured all personnel attended morning safety briefing",
                "contractor team completed housekeeping before demobilisation",
                "vehicle pre-trip inspection checklist filled diligently"
            ],
            "energy_objects": ["work area"]
        }
    ]

    count = len(dataset)
    
    # Calculate how many SIF vs non-SIF we need
    # Current seeds: count SIF vs non-SIF
    seed_sif = sum(1 for d in dataset if d["ground_truth"]["sif_potential"])
    seed_nonsif = count - seed_sif
    
    # Target: ~37% SIF overall
    target_sif_total = int(total_count * 0.37)
    target_nonsif_total = total_count - target_sif_total
    
    needed_sif = max(0, target_sif_total - seed_sif)
    needed_nonsif = max(0, target_nonsif_total - seed_nonsif)

    # Generate SIF records
    for _ in range(needed_sif):
        tmpl = random.choice(sif_templates)
        site = random.choice(SITES)
        act = random.choice(ACTIVITIES)
        ctrl = random.choice(tmpl["control_issues"])
        obj = random.choice(tmpl["energy_objects"])
        
        narrative = tmpl["template"].format(activity=act, site=site, control_issue=ctrl, energy_object=obj)
        
        # Add occasional code-mix (~20%)
        if random.random() < 0.20:
            cm_orig, cm_trans = random.choice(CODE_MIX_CUES)
            narrative += f" Field Note: {cm_trans}."

        # Filer severity distribution for SIF records: 40% Low, 25% Medium, 35% High
        sev_roll = random.random()
        if sev_roll < 0.40:
            filer_sev = "Low"
        elif sev_roll < 0.65:
            filer_sev = "Medium"
        else:
            filer_sev = "High"
        
        # Report type distribution for SIF: 35% UA, 25% UC, 30% Near-Miss, 10% Incident
        rt_roll = random.random()
        if rt_roll < 0.35:
            report_type = "UA"
        elif rt_roll < 0.60:
            report_type = "UC"
        elif rt_roll < 0.90:
            report_type = "Near-Miss"
        else:
            report_type = "Incident"

        record = {
            "report_id": f"OIL-2026-{1000 + count}",
            "timestamp": f"2026-{random.choice(['06','07','08'])}-{random.randint(1, 28):02d}T{random.randint(7, 19):02d}:{random.randint(10, 59):02d}:00Z",
            "site": site,
            "activity": act,
            "report_type": report_type,
            "narrative": narrative,
            "filer_severity": filer_sev,
            "ground_truth": {
                "energy_source": tmpl["energy_source"],
                "control_status": tmpl["control_status"],
                "sif_potential": True,
                "life_saving_rules": tmpl["lsrs"],
                "barrier_failure_category": tmpl["barrier"]
            }
        }
        dataset.append(record)
        count += 1

    # Generate non-SIF records (mix of safe high-energy and low-energy)
    for _ in range(needed_nonsif):
        # 40% safe high-energy, 60% low-energy/minor
        if random.random() < 0.40:
            tmpl = random.choice(safe_high_energy_templates)
        else:
            tmpl = random.choice(low_energy_templates)
        
        site = random.choice(SITES)
        act = random.choice(ACTIVITIES)
        ctrl = random.choice(tmpl["control_issues"])
        obj = random.choice(tmpl["energy_objects"])
        
        narrative = tmpl["template"].format(activity=act, site=site, control_issue=ctrl, energy_object=obj)
        
        # Report type for non-SIF: 40% UA, 40% UC, 15% Near-Miss, 5% Incident
        rt_roll = random.random()
        if rt_roll < 0.40:
            report_type = "UA"
        elif rt_roll < 0.80:
            report_type = "UC"
        elif rt_roll < 0.95:
            report_type = "Near-Miss"
        else:
            report_type = "Incident"

        record = {
            "report_id": f"OIL-2026-{1000 + count}",
            "timestamp": f"2026-{random.choice(['06','07','08'])}-{random.randint(1, 28):02d}T{random.randint(7, 19):02d}:{random.randint(10, 59):02d}:00Z",
            "site": site,
            "activity": act,
            "report_type": report_type,
            "narrative": narrative,
            "filer_severity": "Low",
            "ground_truth": {
                "energy_source": tmpl["energy_source"],
                "control_status": tmpl["control_status"],
                "sif_potential": False,
                "life_saving_rules": tmpl["lsrs"],
                "barrier_failure_category": tmpl["barrier"]
            }
        }
        dataset.append(record)
        count += 1
    
    # Shuffle to avoid ordering bias
    random.shuffle(dataset)

    return dataset

if __name__ == "__main__":
    random.seed(42)
    os.makedirs("data", exist_ok=True)
    ds = generate_dataset(250)
    with open("data/dataset.json", "w", encoding="utf-8") as f:
        json.dump(ds, f, indent=2)
    
    sif_count = sum(1 for d in ds if d["ground_truth"]["sif_potential"])
    nonsif_count = len(ds) - sif_count
    
    # Severity distribution
    sev_dist = {}
    for d in ds:
        s = d.get("filer_severity", "?")
        sev_dist[s] = sev_dist.get(s, 0) + 1
    
    # Report type distribution
    rt_dist = {}
    for d in ds:
        rt = d.get("report_type", "?")
        rt_dist[rt] = rt_dist.get(rt, 0) + 1

    print(f"Dataset generated with {len(ds)} safety reports.")
    print(f"SIF-Potential Precursors: {sif_count} ({sif_count/len(ds)*100:.1f}%)")
    print(f"Non-SIF / Safe: {nonsif_count} ({nonsif_count/len(ds)*100:.1f}%)")
    print(f"Severity Distribution: {sev_dist}")
    print(f"Report Type Distribution: {rt_dist}")
