using System;
using UnityEngine;
using UnityEngine.InputSystem;

// Runs the timing mini-game that prepares a customer's soba before it can be served.
// Angles are in degrees, measured clockwise from the top of the dial.
public class SobaSkillCheck : MonoBehaviour
{
    [SerializeField, Min(1)] private int requiredSuccesses = 3;
    [SerializeField, Min(1)] private int allowedFailures = 3;
    [Tooltip("Fraction of the circle covered by the target zone.")]
    [SerializeField, Range(0.02f, 0.5f)] private float targetZoneSize = 0.1f;
    [Tooltip("Needle speed in degrees per second.")]
    [SerializeField, Min(1f)] private float rotationSpeed = 270f;
    [Tooltip("Minimum distance, in degrees, between the needle and a newly placed zone.")]
    [SerializeField, Range(0f, 180f)] private float minZoneLead = 90f;
    [SerializeField, Min(0f)] private float feedbackDuration = 0.6f;

    private Customer customer;
    private bool isActive;
    private bool clockwise;
    private float feedbackTimer;

    public bool IsActive => isActive;
    public int Successes { get; private set; }
    public int Failures { get; private set; }
    public int RequiredSuccesses => requiredSuccesses;
    public int AllowedFailures => allowedFailures;
    public float TargetZoneSize => targetZoneSize;
    public float NeedleAngle { get; private set; }
    public float ZoneStartAngle { get; private set; }

    public event Action Started;
    public event Action AttemptStarted;
    public event Action<bool> AttemptResolved;
    public event Action Ended;

    public bool Begin(Customer target)
    {
        if (isActive || target == null
            || target.CurrentState != Customer.State.WaitingForFood || target.IsOrderPrepared)
        {
            return false;
        }

        customer = target;
        customer.StateChanged += HandleCustomerStateChanged;
        isActive = true;
        Successes = 0;
        Failures = 0;
        NeedleAngle = 0f;

        Started?.Invoke();
        StartAttempt();
        return true;
    }

    public void Cancel()
    {
        if (isActive)
        {
            End();
        }
    }

    private void OnDisable()
    {
        Cancel();
    }

    private void Update()
    {
        if (!isActive)
        {
            return;
        }

        if (customer == null)
        {
            End();
            return;
        }

        if (feedbackTimer > 0f)
        {
            feedbackTimer -= Time.deltaTime;
            if (feedbackTimer <= 0f)
            {
                AdvanceAfterFeedback();
            }
            return;
        }

        float step = rotationSpeed * Time.deltaTime;
        NeedleAngle = Mathf.Repeat(NeedleAngle + (clockwise ? step : -step), 360f);

        Keyboard keyboard = Keyboard.current;
        if (keyboard != null && keyboard.spaceKey.wasPressedThisFrame)
        {
            Resolve(IsNeedleInZone());
        }
    }

    private void StartAttempt()
    {
        clockwise = UnityEngine.Random.value < 0.5f;

        float zoneDegrees = targetZoneSize * 360f;
        float maxLead = Mathf.Max(minZoneLead, 360f - zoneDegrees - minZoneLead);
        float lead = UnityEngine.Random.Range(minZoneLead, maxLead);
        ZoneStartAngle = clockwise
            ? Mathf.Repeat(NeedleAngle + lead, 360f)
            : Mathf.Repeat(NeedleAngle - lead - zoneDegrees, 360f);

        AttemptStarted?.Invoke();
    }

    private bool IsNeedleInZone()
    {
        return Mathf.Repeat(NeedleAngle - ZoneStartAngle, 360f) <= targetZoneSize * 360f;
    }

    private void Resolve(bool success)
    {
        if (success)
        {
            Successes++;
        }
        else
        {
            Failures++;
        }

        feedbackTimer = Mathf.Max(feedbackDuration, Mathf.Epsilon);
        AttemptResolved?.Invoke(success);
    }

    private void AdvanceAfterFeedback()
    {
        Customer target = customer;

        if (Successes >= requiredSuccesses)
        {
            End();
            target.TryMarkOrderPrepared();
        }
        else if (Failures >= allowedFailures)
        {
            End();
            target.TryLeaveUnserved();
        }
        else
        {
            StartAttempt();
        }
    }

    private void HandleCustomerStateChanged(Customer changed)
    {
        if (changed.CurrentState != Customer.State.WaitingForFood)
        {
            End();
        }
    }

    private void End()
    {
        if (customer != null)
        {
            customer.StateChanged -= HandleCustomerStateChanged;
        }

        customer = null;
        isActive = false;
        feedbackTimer = 0f;
        Ended?.Invoke();
    }
}
