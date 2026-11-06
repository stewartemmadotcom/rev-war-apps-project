"""Tests for clean_text.py, using snippets from real transcriptions
(S34621, W4666, W9546)."""

from clean_text import (clean, extract_notes, strip_brackets, strip_header, strip_page_markers,
                        transcriber, widow_material,
                        strip_trailing_note)

HEADER = (
    "Southern Campaign American Revolution Pension Statements & Rosters\n\n"
    "Pension Application of Edward Abbey S34621\n"
    "        Transcribed and annotated by C. Leon Harris\n\n"
)


def test_header_removed():
    assert strip_header(HEADER + "Record of the pleas").strip() == "Record of the pleas"


def test_sic_keeps_original_spelling():
    text = "under command of Lord Cornwallace [sic: Cornwallis] from"
    assert " ".join(strip_brackets(text).split()) == "under command of Lord Cornwallace from"


def test_multiline_bracket_removed():
    text = "a place called Newrochell [sic:\nNew Rochelle NY]. I was at"
    assert " ".join(strip_brackets(text).split()) == "a place called Newrochell . I was at"


def test_omission_and_date_notes_removed():
    text = "Abbey\n[Certifications omitted.]\nI Edward Abbey in Trenton [26 Dec 1776] and"
    assert "omitted" not in strip_brackets(text)
    assert "1776" not in strip_brackets(text)


def test_nested_brackets_removed():
    assert strip_brackets("a [note [p 3] inside] b").split() == ["a", "b"]


def test_trailing_note_removed_only_near_end():
    body = "declaration text " * 50
    assert strip_trailing_note(body + "\nNOTE: transcriber comment").strip() == body.strip()
    early = "NOTE: early\n" + body
    assert strip_trailing_note(early) == early


def test_full_clean():
    raw = HEADER + "The State of Mississippi }   Circuit Court\nI was in the 3 rd Virginia “regiment”"
    assert clean(raw) == 'The State of Mississippi Circuit Court\nI was in the 3rd Virginia "regiment"'


def test_graves_header_removed():
    raw = ("Southern Campaigns American Revolution Pension Statements & Rosters \n"
           "Pension application of George Earnest W4666  \nKatharine Earnest \nf56Va \n"
           "Transcribed by Fred Weyler; corrected and annotated by Will Graves \n"
           "rev'd 2/26/26 \n(p 4) State of Georgia \n")
    assert clean(raw) == "State of Georgia"


def test_page_markers_removed():
    text = "(p 4) State of Georgia (p6) Genl Nelson (pp. 3-4) end"
    assert strip_page_markers(text).split() == ["State", "of", "Georgia", "Genl", "Nelson", "end"]


def test_unclosed_bracket_removed_to_end_of_paragraph():
    text = "before\n[pp. 3-4 contains the family record.\nstill note\n\nnext paragraph"
    assert strip_brackets(text).split() == ["before", "next", "paragraph"]


def test_addendum_header_removed_and_note_ends_at_addendum():
    # W10001: Graves file, then a Harris addendum with its own header
    raw = (HEADER + "declaration text " * 50 + "\nNOTE: The widow was pensioned.\n"
           "Southern Campaign American Revolution Pension Statements and Rosters\n"
           "Addendum to Benjamin Wilkerson (Wilkinson) W10001\n"
           "Transcribed and annotated by C. Leon Harris. 29 April 2023.\n"
           "Benjamin Wilkerson late a soldier in the 2 Virg. State Reg't.")
    cleaned = clean(raw)
    assert "Southern Campaign" not in cleaned and "Addendum" not in cleaned
    assert "pensioned" not in cleaned
    assert cleaned.endswith("Benjamin Wilkerson late a soldier in the 2 Virg. State Reg't.")
    assert extract_notes(raw) == ["NOTE: The widow was pensioned."]


def test_audited_account_header_url_and_rule_removed():
    # W10 and W10096
    raw = ("text before\n_____________________________\n"
           "South Carolina Audited Accounts relating to Samuel Hand\npp5\n"
           "Audited Account No. 3293A\nTranscribed by Will Graves\n3/4/22\n"
           "https://www.fold3.com/image/616518609\n$40 United States of America (p12 ff)")
    assert clean(raw) == "text before\n\n$40 United States of America"


def test_unclosed_label_keeps_period_text():
    # W1425: "[pp 5-6: family record:" is never closed; the record itself is period text
    text = "before\n[pp 5-6: family record:\nBirths\nJohn Hereford was Born the 3rd day of February 1758"
    assert strip_brackets(text).split() == ["before", "Births", "John", "Hereford", "was", "Born",
                                            "the", "3rd", "day", "of", "February", "1758"]
    # W160: a second unclosed label inside the record
    text = "[p 6: family record:\nJohn born 1796\n[p 19: more family register:\nIsaac born 1799"
    assert strip_brackets(text).split() == ["John", "born", "1796", "Isaac", "born", "1799"]
    # W1095: a typo "[[ 12]" leaves a stray "["
    text = "[[ 12]\nState of Tennessee Second Judicial Circuit: On this 1st day of July 1818"
    assert strip_brackets(text).split()[:3] == ["State", "of", "Tennessee"]


def test_unclosed_note_saved_to_notes():
    # W9493: a page summary the transcriber never closed
    raw = (HEADER + "text\n[p 4: On April 24, 1843 Margaret Kelsoe filed for a widow's pension "
           "stating that she is the widow of Alexander Kelsoe\n\nState of Indiana")
    assert "Kelsoe" not in clean(raw)
    assert extract_notes(raw) == ["p 4: On April 24, 1843 Margaret Kelsoe filed for a widow's "
                                  "pension stating that she is the widow of Alexander Kelsoe"]


def test_note_with_nested_bracket_saved_whole():
    # W3060
    raw = (HEADER + "[p 12: On October 4, 1838 Mrs. Elizabeth Beard [sic, Elizabeth Baird], 65, "
           "gave testimony that she was present at the marriage]\n")
    assert extract_notes(raw) == ["p 12: On October 4, 1838 Mrs. Elizabeth Beard , 65, gave "
                                  "testimony that she was present at the marriage"]


def test_insertion_arrows_removed_words_kept():
    assert clean("thirty ↑twenty five ↓ years") == "thirty twenty five years"


def test_notes_keep_page_summaries_and_skip_short_and_sic():
    raw = (HEADER + "Lord Cornwallace [sic: Lord Charles Cornwallis, British commander] and "
           "General [Hugh] Mercer.\n"
           "[p 14: Mary Bagwell, widow, filed for a pension on October 8, 1851.]\n")
    assert extract_notes(raw) == ["p 14: Mary Bagwell, widow, filed for a pension on October 8, 1851."]


def test_notes_include_trailing_note_block():
    body = "declaration text " * 50
    assert extract_notes(body + "\nNOTE: The widow was pensioned in 1838.") == [
        "NOTE: The widow was pensioned in 1838."]


def test_transcriber_names():
    assert transcriber(HEADER) == "C. Leon Harris"
    assert transcriber("Transcribed and annotated by C. Leon Harris. Revised 10 June 2014.") == "C. Leon Harris"
    assert transcriber("Transcribed by Fred Weyler; corrected and annotated by Will Graves") == "Fred Weyler"
    assert transcriber("Transcribed by Will Graves 3/10/09: rev'd 9/16/16") == "Will Graves"


SOLDIER = "he served three months as a private in the militia"


def test_widow_material_transcribed():
    assert widow_material("that she is the widow of John McCool", []) == "transcribed"
    # W3129: no "widow" at all
    assert widow_material("declares that her husband the aforesaid Joseph Allsop died", []) == "transcribed"


def test_widow_material_summary_only():
    assert widow_material(SOLDIER, ["p 15: Mary Abbott, 83, filed for a widows pension"]) == "summary_only"
    # W4897: "made an application ... stating that she married"
    note = ("NOTE: Winney Bishop, 80, of Surry County, made an application for a pension "
            "certified on 18 Dec 1849 stating that she married William Bishop on 10 Sep 1796")
    assert widow_material(SOLDIER, [note]) == "summary_only"


def test_widow_material_heirs_claim():
    # W886 and W9718
    assert widow_material(SOLDIER, ["NOTE: On 7 Jan 1845 Philip Ashlock, 55, applied for a pension "
                                    "as the only surviving child of James Ashlock"]) == "heirs_claim"
    assert widow_material(SOLDIER, ["Ambrose Barnett applied for a pension for himself, brothers, "
                                    "and sisters by right of their mother, Elizabeth Barnett"]) == "heirs_claim"


def test_widow_material_testimony_only():
    # W25334 and W24644
    assert widow_material(SOLDIER, ["Richard Choat and Amos Acre gave testimony that Edith Acre "
                                    "is the widow of William Acre"]) == "testimony_only"
    assert widow_material(SOLDIER, ["that they lived together as husband and wife"]) == "testimony_only"


def test_widow_material_cases_found_by_hand_check():
    # W5348: her own declaration, without "widow"
    assert widow_material("She further declares that her maiden name was Calvert, that she "
                          "intermarried with the said Lieutenant Archer", []) == "transcribed"
    # W514, W1203, W2905: her application or testimony, summarized
    assert widow_material(SOLDIER, ["Elizabeth H Ashe gave testimony that she is the widow of "
                                    "Lieutenant Samuel Ashe"]) == "summary_only"
    assert widow_material(SOLDIER, ["NOTE: On 27 Apr 1848 Nancy Alvis, 71, petitioned Congress for a "
                                    "pension, stating that as Nancy Bingham she married John Alvis"]) == "summary_only"
    assert widow_material(SOLDIER, ["Her application was supported by a deposition by their "
                                    "daughter, America Hawkins."]) == "summary_only"
    # W18566, W9359: heirs' declarations in period language
    assert widow_material("That his widow Mary Bolick died about the 9th of October in the year "
                          "A.D. 1838.", []) == "heirs_claim"
    assert widow_material("Joseph Black in behalf of himself and the other heirs of said John "
                          "Black 2d, deceased", []) == "heirs_claim"
    # W68: family record
    assert widow_material("Thomas Bledsoe and Marget Bledsoe was married November the 6th 1787",
                          []) == "testimony_only"


def test_heirs_declaration_citing_widows_act_is_not_hers():
    # W9771 and W276: children/administrator claiming under the widows' acts
    assert widow_material("make the following declaration in order to obtain the benefit of the "
                          "Acts of Congress passed 7 July 1836 granting pensions to certain widows. "
                          "To Wit: that they are the children of Susan Callaway deceased who was "
                          "the widow of James Callaway", []) == "heirs_claim"
    assert widow_material("doth on his oath make the following Declaration in order to obtain for "
                          "the children of Mary Anderson deceased the benefit of the provision made "
                          "by the Acts of Congress", []) == "heirs_claim"


def test_son_as_witness_does_not_hide_widow_declaration():
    # W5623: the widow declares; her son swears in support
    assert widow_material("to obtain the benefit of the provision made by the act of Congress "
                          "passed July 4th, 1836. That she is the widow of John Andrew. ... "
                          "who after being duly sworn upon oath saith that he is the son of "
                          "Mary O. Andrew", []) == "transcribed"


def test_widow_material_cases_found_by_round2_check():
    # W1954, W9806, W21645: her application, summarized in other words
    assert widow_material(SOLDIER, ["p 21: Mrs. Mary Taylor made oath that she is the widow of "
                                    "the late James Taylor"]) == "summary_only"
    assert widow_material(SOLDIER, ["On 19 Jan 1858 Elizabeth Corbett, 62 or 63, stated that as "
                                    "Elizabeth Blake she was married to John Corbett"]) == "summary_only"
    assert widow_material(SOLDIER, ["the widow, 67, a resident of the 3rd District in the state of "
                                    "Tennessee file for the restoration of her pension"]) == "summary_only"
    # W7482, W5325: a woman witness, not the widow
    assert widow_material(SOLDIER, ["Mary Westbrook gave testimony that she was well acquainted "
                                    "with Samuel Morrow"]) == "none"
    assert widow_material(SOLDIER, ["Mary Coffman, 65, gave testimony that she was well acquainted "
                                    "with Jacob Lineweaver and Margaret Pickle prior to their "
                                    "marriage"]) == "testimony_only"
    # W9981: "files for a widow's pension"
    assert widow_material(SOLDIER, ["Jane McGaughey, 78, files for a widow's pension stating that "
                                    "she is the widow of Samuel McGaughey"]) == "summary_only"
    # W9418, W19182: heirs' claims in other words
    assert widow_material(SOLDIER, ["Robert W. Durham, filed a claim as the son of Charnel Durham "
                                    "and Nancy Durham"]) == "heirs_claim"
    assert widow_material(SOLDIER, ["Mary B. Perry applied for the balance of pension due to her "
                                    "father, and for a pension in the name of her mother"]) == "heirs_claim"
    # W9098
    assert widow_material(SOLDIER, ["Frankey Kendrick, the widow of Benjamin Kendrick died November "
                                    "9, 1838 survived by the following children and heirs"]) == "heirs_claim"
    # W4233: a transcriber noting the widow's death is not an heirs' claim
    assert widow_material(SOLDIER, ["Facts in file: the widow died May 25, 1840"]) == "none"
    # W2823, W18824, W876: testimony about her
    assert widow_material(SOLDIER, ["Jacob Maddox gave testimony in support of the application of "
                                    "his mother Elizabeth Maddox"]) == "testimony_only"
    assert widow_material(SOLDIER, ["Sterling Rose testified that he was at the marriage of his "
                                    "brother John to the applicant Rachel Rose."]) == "testimony_only"
    assert widow_material(SOLDIER, ["Bird Thomas verified the family record now in possession of "
                                    "Catharine Thomas widow of John Thomas"]) == "testimony_only"


def test_trailing_note_with_semicolon():
    # W19769
    body = "declaration text " * 50
    assert strip_trailing_note(body + "\nNOTE; On 17 Feb 1840 Lovia Hight applied").strip() == body.strip()


def test_widow_material_none():
    assert widow_material(SOLDIER, ["His widow was pensioned in a like amount commencing on "
                                    "February 19, 1840 and ending on November 1st, 1842 when "
                                    "she died"]) == "none"
    assert widow_material(SOLDIER, ["Veteran was pensioned at $34.88. His widow was pensioned "
                                    "in a like amount."]) == "none"
    assert widow_material(SOLDIER, ["Col. Taylor commanded the guard regiment."]) == "none"
