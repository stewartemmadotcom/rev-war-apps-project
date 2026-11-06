"""Tests for split_documents.py, using snippets from real cleaned files
(W4069, W5873)."""

from split_documents import doc_type, split

WIDOW = (
    "State of North Carolina, Caswell County\n"
    "On this the 1st day of June 1840 personally appeared before the Undersigned one of the Justices\n"
    "Elizabeth Slade a resident of the aforesaid County aged 76 years, who being first duly sworn\n"
    "according to Law, doth, on her oath, make the following declaration. That she is the widow of\n"
    "William Slade Senior. That her husband the aforesaid William Slade died in 1836.\n"
    "Sworn to and subscribed, on the day and year above written, before the George W Bannerman,\n"
    "Richard S Gillespie and Durham Lewis Justices holding the court.\n"
    "S/ Elizabeth Slade, X her mark\n")
WITNESS = (
    "Richard Cheshire being duly sworn upon the Holy Evangelist of Almighty God deposeth and\n"
    "saith as follows to wit: I was acquainted with Richard Brown during the war of the Revolution:\n"
    "he continued in service six months.\n"
    "S/ Richard Cheshire, X his mark\n"
    "Subscribed and sworn to before me this 5th day of November 1845\n"
    "S/ K. S. Gillespie, JP\n")
COURT = (
    "above Stated. See affidavit A.\n"
    "State of North Carolina Caswell County: Superior Court of Law November Term 1832\n"
    "Personally appeared in open Court before the Honorable James Martin, now in Session, Daniel\n"
    "Merritt, who being duly Sworn, Deposeth and saith that he was a Soldier of the Army\n")


def test_splits_after_signature_and_keeps_jurat_with_its_document():
    docs = split(WIDOW + WITNESS)
    assert len(docs) == 2
    assert docs[0][1].endswith("S/ Elizabeth Slade, X her mark")
    assert docs[1][1].startswith("Richard Cheshire being duly sworn")


def test_heading_after_a_sentence_starts_a_document():
    docs = split(COURT)
    assert [d[1].split("\n")[0] for d in docs] == [
        "above Stated. See affidavit A.",
        "State of North Carolina Caswell County: Superior Court of Law November Term 1832"]


def test_capitalized_heading_starts_a_document():
    # W18643
    text = ("S/ Anderson Brightwell, X his mark\nSTATE OF VIRGINIA,\nPittsylvania COUNTY, TO WIT:\n"
            "ON this 3 day of November 1839 personally appeared Nancy Brightwell\n")
    docs = split(text)
    assert docs[-1][1].startswith("STATE OF VIRGINIA,\nPittsylvania COUNTY")


def test_county_in_mid_sentence_does_not_split():
    text = ("he volunteered himself in the service from the said\n"
            "County and over Dan River in the State of Virginia and Joined the army\n")
    assert len(split(text)) == 1


def test_document_types():
    assert doc_type(WIDOW) == "widow_declaration"
    assert doc_type(WITNESS) == "testimony"
    # a woman witness is not the widow
    assert doc_type("Mary Westbrook being sworn doth on her oath say that she was well acquainted "
                    "with Samuel Morrow and Lydia his wife. S/ Mary Westbrook, X her mark") == "testimony"
    # W8377: a son claiming after his mother's death
    assert doc_type("made oath to the following Declaration; to wit, that he is the son of William "
                    "Booton and Amelia Booton both now deceased, that she remained the widow") == "heirs_claim"
    # W26946: the oath formula broken across lines
    assert doc_type("Keziah Reid aged seventy-six years, who being first duly sworn doth on her\n"
                    "oath make the following declaration. That she is the widow of John Reid") == "widow_declaration"
    # W9166: a clerk's "his" for the widow
    assert doc_type("personally appeared Sarah Williams of Kershaw District, widow of William "
                    "Williams, who being first duly sworn doth on his oath make the following "
                    "declaration. Declarant states that her husband enlisted") == "widow_declaration"
    # W5119: a justice's certificate about her Bible record
    assert doc_type("Fauquier County to wit I Joseph Chilton a Justice of the peace in the County "
                    "aforesaid do certify that Isham Keith this day exhibited a Bible in which her "
                    "husband's marriage is entered") == "record"
    assert doc_type("doth on his oath make the following declaration in order to obtain the benefit "
                    "of the act of Congress passed June 7, 1832. He hereby relinquishes every claim "
                    "whatever to a pension") == "soldier_declaration"
