import pytest

from app.normalization.skills import SkillExtractor


@pytest.fixture
def extractor():
    return SkillExtractor(
        {
            "Java": ["java"],
            "Spring Boot": ["spring boot"],
            "REST APIs": [
                "rest api",
                "rest apis",
                "restful api",
                "restful apis",
            ],
            "PostgreSQL": ["postgresql", "postgres"],
            "Docker": ["docker"],
            "React": ["react", "react.js", "reactjs"],
            "TypeScript": ["typescript"],
            "JWT Authentication": [
                "jwt",
                "json web token",
                "json web tokens",
            ],
            "Node.js": ["node.js", "nodejs", "node js"],
        }
    )


def test_extracts_canonical_skills(extractor):
    text = """
    We build backend services using Java, Spring Boot,
    PostgreSQL, Docker and REST APIs.
    """

    assert extractor.extract(text) == [
        "Java",
        "Spring Boot",
        "REST APIs",
        "PostgreSQL",
        "Docker",
    ]


def test_extracts_skill_aliases(extractor):
    text = """
    Experience with Postgres, RESTful APIs, ReactJS,
    NodeJS, TypeScript and JWT.
    """

    assert extractor.extract(text) == [
        "REST APIs",
        "PostgreSQL",
        "React",
        "TypeScript",
        "JWT Authentication",
        "Node.js",
    ]


def test_matching_is_case_insensitive(extractor):
    text = "JAVA, SPRING BOOT, POSTGRESQL and DOCKER"

    assert extractor.extract(text) == [
        "Java",
        "Spring Boot",
        "PostgreSQL",
        "Docker",
    ]


def test_duplicate_mentions_are_removed(extractor):
    text = """
    Java developer.
    Strong Java experience.
    Java and Spring Boot.
    """

    assert extractor.extract(text) == [
        "Java",
        "Spring Boot",
    ]


def test_empty_text_returns_empty_list(extractor):
    assert extractor.extract("") == []
    assert extractor.extract(None) == []


def test_partial_words_do_not_match(extractor):
    text = """
    JavaScript is useful.
    GitHub is used for source control.
    """

    skills = extractor.extract(text)

    assert "Java" not in skills


def test_rejects_empty_vocabulary():
    with pytest.raises(ValueError, match="cannot be empty"):
        SkillExtractor({})


def test_rejects_empty_aliases():
    with pytest.raises(
        ValueError,
        match="must have at least one alias",
    ):
        SkillExtractor({"Java": []})


def test_rejects_string_aliases():
    with pytest.raises(
        ValueError,
        match="must be a sequence",
    ):
        SkillExtractor({"Java": "java"})
