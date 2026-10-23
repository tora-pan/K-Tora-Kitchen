using UnityEngine;

[CreateAssetMenu(fileName = "NewRecipe", menuName = "K-Tora/Recipe")]
public class RecipeData : ScriptableObject
{
    [SerializeField] private string displayName = "Soba";
    [SerializeField, Min(0)] private int price = 600;

    public string DisplayName => displayName;
    public int Price => price;
}
