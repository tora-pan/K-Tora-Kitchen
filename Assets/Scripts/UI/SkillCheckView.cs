using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class SkillCheckView : MonoBehaviour
{
    [SerializeField] private SobaSkillCheck skillCheck;
    [SerializeField] private GameObject panel;
    [SerializeField] private RectTransform needle;
    [SerializeField] private Image targetZone;
    [SerializeField] private TMP_Text progressText;
    [SerializeField] private TMP_Text mistakesText;
    [SerializeField] private TMP_Text feedbackText;
    [SerializeField] private Color zoneColor = new Color(0.2f, 0.85f, 0.3f);
    [SerializeField] private Color successColor = new Color(1f, 0.9f, 0.3f);
    [SerializeField] private Color failureColor = new Color(0.95f, 0.25f, 0.2f);
    [SerializeField, Min(0.01f)] private float feedbackPunchDuration = 0.2f;
    [SerializeField, Min(1f)] private float feedbackPunchScale = 1.4f;

    private float feedbackAge;

    private void Awake()
    {
        if (!HasReferences())
        {
            Debug.LogError("SkillCheckView is missing Inspector references.", this);
            enabled = false;
        }
    }

    private void OnEnable()
    {
        if (!HasReferences())
        {
            return;
        }

        skillCheck.Started += Show;
        skillCheck.AttemptStarted += ShowAttempt;
        skillCheck.AttemptResolved += ShowResult;
        skillCheck.Ended += Hide;

        panel.SetActive(skillCheck.IsActive);
    }

    private void OnDisable()
    {
        if (skillCheck != null)
        {
            skillCheck.Started -= Show;
            skillCheck.AttemptStarted -= ShowAttempt;
            skillCheck.AttemptResolved -= ShowResult;
            skillCheck.Ended -= Hide;
        }

        Hide();
    }

    private void Update()
    {
        if (!skillCheck.IsActive)
        {
            return;
        }

        needle.localEulerAngles = new Vector3(0f, 0f, -skillCheck.NeedleAngle);

        if (feedbackAge < feedbackPunchDuration)
        {
            feedbackAge += Time.deltaTime;
            float scale = Mathf.Lerp(feedbackPunchScale, 1f, feedbackAge / feedbackPunchDuration);
            feedbackText.rectTransform.localScale = Vector3.one * scale;
        }
    }

    private bool HasReferences()
    {
        return skillCheck != null && panel != null && needle != null && targetZone != null
            && progressText != null && mistakesText != null && feedbackText != null;
    }

    private void Show()
    {
        panel.SetActive(true);
        UpdateCounts();
    }

    private void Hide()
    {
        if (panel != null)
        {
            panel.SetActive(false);
        }
    }

    private void ShowAttempt()
    {
        targetZone.fillAmount = skillCheck.TargetZoneSize;
        targetZone.rectTransform.localEulerAngles = new Vector3(0f, 0f, -skillCheck.ZoneStartAngle);
        targetZone.color = zoneColor;
        feedbackText.text = string.Empty;
        UpdateCounts();
    }

    private void ShowResult(bool success)
    {
        Color color = success ? successColor : failureColor;
        targetZone.color = color;
        feedbackText.color = color;
        feedbackText.text = success ? "Perfect!" : "Missed!";
        feedbackAge = 0f;
        UpdateCounts();
    }

    private void UpdateCounts()
    {
        progressText.text = $"Skill Checks: {skillCheck.Successes} / {skillCheck.RequiredSuccesses}";
        mistakesText.text = $"Mistakes: {skillCheck.Failures} / {skillCheck.AllowedFailures}";
    }
}
