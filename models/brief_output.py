from pydantic import BaseModel

class BriefLine(BaseModel):
    #One of the narrated brief text , with the face it's
    #grounded in . source_ref must be an item id that exists in the
    # BriefFacts this was generated from , validated seperately in
    # the reference-or-drop, not here.
    
    text: str
    source_ref: str
    
class NarratedBrief(BaseModel):
    #The model's full structured output for one section of the
    #(eg: one person's status or the blockers section)
    
    lines: list[BriefLine]