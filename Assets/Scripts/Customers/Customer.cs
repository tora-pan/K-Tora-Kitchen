using System;
using UnityEngine;

public class Customer : MonoBehaviour
{
    public enum State
    {
        WalkingToCounter,
        Ordering,
        WaitingForFood,
        Paying,
        Leaving
    }

    [SerializeField, Min(0.1f)] private float walkSpeed = 2f;
    [SerializeField, Min(0f)] private float turnSpeed = 720f;
    [SerializeField, Min(0f)] private float orderDuration = 1f;
    [SerializeField, Min(0f)] private float payDuration = 1f;

    private const float ArrivalDistance = 0.01f;

    private Transform counterPoint;
    private Transform exitPoint;
    private CashRegister cashRegister;
    private float stateTimer;

    public State CurrentState { get; private set; }
    public RecipeData Order { get; private set; }
    public bool IsOrderPrepared { get; private set; }
    public bool LeftUnserved { get; private set; }

    public event Action<Customer> StateChanged;
    public event Action<Customer> Left;

    public void Initialize(RecipeData order, Transform counterPoint, Transform exitPoint, CashRegister cashRegister)
    {
        Order = order;
        this.counterPoint = counterPoint;
        this.exitPoint = exitPoint;
        this.cashRegister = cashRegister;
        EnterState(State.WalkingToCounter);
    }

    private void Start()
    {
        if (Order == null || counterPoint == null || exitPoint == null || cashRegister == null)
        {
            Debug.LogError("Customer was not initialized with all required references.", this);
            enabled = false;
        }
    }

    private void Update()
    {
        switch (CurrentState)
        {
            case State.WalkingToCounter:
                if (MoveTowards(counterPoint.position))
                {
                    EnterState(State.Ordering, orderDuration);
                }
                break;

            case State.Ordering:
                FaceCounter();
                if (TickTimer())
                {
                    EnterState(State.WaitingForFood);
                }
                break;

            case State.WaitingForFood:
                FaceCounter();
                break;

            case State.Paying:
                FaceCounter();
                if (TickTimer())
                {
                    cashRegister.AddCash(Order.Price);
                    EnterState(State.Leaving);
                }
                break;

            case State.Leaving:
                if (MoveTowards(exitPoint.position))
                {
                    Left?.Invoke(this);
                    Destroy(gameObject);
                }
                break;
        }
    }

    public bool TryMarkOrderPrepared()
    {
        if (CurrentState != State.WaitingForFood || IsOrderPrepared)
        {
            return false;
        }

        IsOrderPrepared = true;
        StateChanged?.Invoke(this);
        return true;
    }

    public bool TryServe()
    {
        if (CurrentState != State.WaitingForFood || !IsOrderPrepared)
        {
            return false;
        }

        EnterState(State.Paying, payDuration);
        return true;
    }

    public bool TryLeaveUnserved()
    {
        if (CurrentState != State.WaitingForFood)
        {
            return false;
        }

        LeftUnserved = true;
        EnterState(State.Leaving);
        return true;
    }

    private void EnterState(State newState, float duration = 0f)
    {
        CurrentState = newState;
        stateTimer = duration;
        StateChanged?.Invoke(this);
    }

    private bool TickTimer()
    {
        stateTimer -= Time.deltaTime;
        return stateTimer <= 0f;
    }

    private bool MoveTowards(Vector3 target)
    {
        target.y = transform.position.y;
        Vector3 toTarget = target - transform.position;
        if (toTarget.sqrMagnitude > ArrivalDistance * ArrivalDistance)
        {
            TurnTowards(toTarget);
        }

        transform.position = Vector3.MoveTowards(transform.position, target, walkSpeed * Time.deltaTime);
        return (transform.position - target).sqrMagnitude <= ArrivalDistance * ArrivalDistance;
    }

    // CounterPoint's forward (blue) axis points at the truck; rotate it in the scene to change where customers look.
    private void FaceCounter()
    {
        TurnTowards(counterPoint.forward);
    }

    private void TurnTowards(Vector3 direction)
    {
        direction.y = 0f;
        if (direction.sqrMagnitude < Mathf.Epsilon)
        {
            return;
        }

        Quaternion facing = Quaternion.LookRotation(direction);
        transform.rotation = Quaternion.RotateTowards(transform.rotation, facing, turnSpeed * Time.deltaTime);
    }
}
