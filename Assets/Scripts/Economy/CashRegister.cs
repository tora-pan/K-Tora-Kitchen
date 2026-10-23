using System;
using UnityEngine;

public class CashRegister : MonoBehaviour
{
    [SerializeField, Min(0)] private int cash;

    public int Cash => cash;

    public event Action<int> CashChanged;

    public void AddCash(int amount)
    {
        if (amount <= 0)
        {
            Debug.LogWarning($"Ignored non-positive cash amount: {amount}", this);
            return;
        }

        cash += amount;
        CashChanged?.Invoke(cash);
    }
}
