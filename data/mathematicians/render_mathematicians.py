"""
Render mathematicians data to HTML format.
"""
def make_title(data):
    birth_year = data.get('birth_year', 'Unknown')
    death_year = data.get('death_year', 'Present')
    lifespan = f"({birth_year} - {death_year})"
    return f"{data['name']} {lifespan}"
