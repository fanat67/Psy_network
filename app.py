import pandas as pd
from flask import Flask, render_template
from collections import OrderedDict
import os

app = Flask(__name__)

# --- MASTER HIERARCHIES (Single Source of Truth) ---
METHOD_HIERARCHY_RAW = {
    "mixed": ["Mixed-methods", "theoretical analysis", "conceptual analysis"],
    "Quan": ["surveys", "questionnaires", "Advanced stats", "observational studies", "correlational data", "quantitative analysis", "longitudinal data", "dyadic analyses", "multilevel studies", "scale development", "confirmatory factor analysis", "Intervention trials", "Big Data"],
    "Qualitative": ["focus groups", "talanoa", "qualitative analyses", "thematic analysis", "open-ended questions", "content analysis", "interviews", "clinical interviews"],
    "Lab experiments (instruments)": ["Experiments", "eye tracking", "VR", "TMS", "EEG / ERP", "Physiological measures", "psychophysiological measures", "Animal Research"],
    "Behavioural experiments (no instruments)": ["behavioural experiments", "behavioural observations", "Computerized cognitive tasks", "social interaction tasks", "human-AI interaction", "Non-neuroscientific equipment"]
}

TOPIC_HIERARCHY_RAW = {
    "Education": ["Social learning"], "Cognition": ["Social cognition", "Mind perception", "Person perception", "Theory of mind", "Psychopathy", "Attention", "executive function", "Human AI interaction", "Automatic Processes", "Controlled Processes", "Causal", "Psychadelic", "Animal Behaviour", "Neuro plasticity", "Trauma"],
    "Developmental": ["Child Development", "Youth", "Youth Offending", "Brain development", "Animal Behaviour"], "Cultural": ["Pacific", "culture"],
    "Psychopathology/MH": ["Psychopathy", "self injury", "suicide", "psychosis", "postpartum", "early intervention", "mental health", "Psychopharmacology", "Drugs", "Trauma"], "Stereotypes": ["prejudice", "discrimination"],
    "Perception": [], "Memory": ["Autobiographical memory", "Human Memory", "Episodic memory", "Priming memory", "Implicit memory", "Recognition Memory", "Memory Face", "Location memory", "Time based memory", "Neuro plasticity"],
    "Emotion": ["Emotion regulation", "Emotion socialization", "Emotion expression", "Lovingness (affective quality)", "Agression", "Empathy", "Emotions", "Psychopathy"], "Forensic": ["Psychopathy", "Justice involvement"],
    "Theoretical": [], "Identity": ["Dehumanization", "Family Dynamics", "Parenting", "Parent child interactions", "Infants", "Wokeness", "Lovingness (self defining)", "Psychopathy", "Political behaviour", "Religion"],
    "Relationships": ["Family Dynamics", "Intimate relationships", "Parent child interactions"]
}

def clean_text(text):
    return text.replace("Qualatative", "Qualitative").replace("Behvaiourial", "Behavioural").replace("Stereoypes", "Stereotypes").strip()

METHOD_HIERARCHY = OrderedDict((clean_text(k), [clean_text(v) for v in vs]) for k, vs in METHOD_HIERARCHY_RAW.items())
TOPIC_HIERARCHY = OrderedDict((clean_text(k), [clean_text(v) for v in vs]) for k, vs in TOPIC_HIERARCHY_RAW.items())

ALL_OFFICIAL_METHODS = {clean_text(item).lower() for sublist in METHOD_HIERARCHY.values() for item in sublist}
ALL_OFFICIAL_TOPICS = {clean_text(item).lower() for sublist in TOPIC_HIERARCHY.values() for item in sublist}

def load_profiles_from_csv(filepath='HLT - Supervisors.csv'):
    if not os.path.exists(filepath):
        print(f"ERROR: The file '{filepath}' was not found.")
        return None
    try:
        supervisors_df = pd.read_csv(filepath).fillna('')
    except Exception as e:
        print(f"ERROR: Failed to read or process the CSV file. Reason: {e}")
        return None

    supervisor_profiles = {}
    
    def find_matches(raw_text, official_keywords):
        found_keywords = set()
        raw_items = {item.strip().lower() for item in raw_text.replace(';', ',').split(',')}
        for raw_item in raw_items:
            if not raw_item: continue
            for official_keyword in official_keywords:
                if official_keyword in raw_item:
                    found_keywords.add(official_keyword)
        return found_keywords

    for _, row in supervisors_df.iterrows():
        name = row['Name']
        specific_methods = find_matches(row['Methods'], ALL_OFFICIAL_METHODS)
        specific_topics = find_matches(row['Research Focus'], ALL_OFFICIAL_TOPICS) 
        hlt_methods = {clean_text(item).lower() for item in row['HLT methods'].replace(';', ',').split(',') if item.strip()}
        hlt_topics = {clean_text(item).lower() for item in row['Higher Level Themes : Research focus'].replace(';', ',').split(',') if item.strip()}

        supervisor_profiles[name] = {
            "Categories": sorted({clean_text(c).lower() for c in row['Discipline/s'].replace(';', ',').split(',') if c.strip()}),
            "Topics": sorted(list(specific_topics.union(hlt_topics))),
            "Methods": sorted(list(specific_methods.union(hlt_methods))),
            "info": f"Focuses on {row['Higher Level Themes : Research focus']}.",
            "contact": "Contact not available",
            "publications": "#"
        }
    return supervisor_profiles

SUPERVISOR_PROFILES = load_profiles_from_csv()

@app.route('/')
def index():
    if SUPERVISOR_PROFILES is None:
        # --- THIS IS THE CORRECT, DETAILED ERROR MESSAGE ---
        return """
        <div style="font-family: sans-serif; padding: 40px;">
            <h1>Error: Could not load data</h1>
            <p>The application was unable to find or read the <code>HLT - Supervisors.csv</code> file.</p>
            <p>Please ensure that:</p>
            <ol>
                <li>The file is named exactly <strong>HLT - Supervisors.csv</strong></li>
                <li>The file is in the <strong>same folder</strong> as your <code>app.py</code> script.</li>
            </ol>
            <p>After fixing the issue, please restart the Python server.</p>
        </div>
        """, 500

    all_categories = sorted({cat for p in SUPERVISOR_PROFILES.values() for cat in p['Categories']})
    
    all_topics_flat = set(TOPIC_HIERARCHY.keys())
    for topics in TOPIC_HIERARCHY.values(): all_topics_flat.update(topics)

    all_methods_flat = set(METHOD_HIERARCHY.keys())
    for methods in METHOD_HIERARCHY.values(): all_methods_flat.update(methods)

    return render_template('index.html',
                           SUPERVISOR_PROFILES=SUPERVISOR_PROFILES,
                           all_categories=all_categories,
                           topic_hierarchy=TOPIC_HIERARCHY,
                           method_hierarchy=METHOD_HIERARCHY,
                           all_topics_flat=[t.lower() for t in sorted(list(all_topics_flat))],
                           all_methods_flat=[m.lower() for m in sorted(list(all_methods_flat))])

if __name__ == '__main__':
    app.run(debug=True)