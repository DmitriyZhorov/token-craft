"""
Token-Craft Pricing Calculator

Calculates costs based on flexible pricing configuration.
Supports multiple deployment methods (Direct API, Bedrock, Vertex).
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple


class PricingCalculator:
    """Calculate token costs across different deployment methods."""

    def __init__(self, pricing_config_path: Optional[Path] = None):
        """
        Initialize pricing calculator.

        Args:
            pricing_config_path: Path to pricing_config.json (optional)
        """
        if pricing_config_path is None:
            pricing_config_path = Path(__file__).parent / "pricing_config.json"

        self.config = self._load_config(pricing_config_path)
        self.deployment_methods = self.config.get("deployment_methods", {})

    def _load_config(self, config_path: Path) -> Dict:
        """Load pricing configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load pricing config: {e}")
            return {}

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
        deployment: str = "direct_api",
        use_cache: bool = False,
        cache_read_tokens: int = 0
    ) -> Dict:
        """
        Calculate cost for given token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model ID (e.g., "claude-sonnet-4-5")
            deployment: Deployment method (direct_api, aws_bedrock, google_vertex)
            use_cache: Whether prompt caching is used
            cache_read_tokens: Number of tokens read from cache

        Returns:
            Dict with cost breakdown
        """
        # Get pricing for deployment method
        deployment_config = self.deployment_methods.get(deployment, {})
        models = deployment_config.get("models", {})
        model_pricing = models.get(model, {})

        if not model_pricing:
            return {
                "error": f"Model {model} not found in {deployment}",
                "total_cost": 0,
                "breakdown": {}
            }

        # Get prices (per million tokens)
        input_price = model_pricing.get("input_price")
        output_price = model_pricing.get("output_price")
        cache_write_price = model_pricing.get("cache_write_price")
        cache_read_price = model_pricing.get("cache_read_price")

        if input_price is None or output_price is None:
            return {
                "error": f"Pricing not available for {model} on {deployment}",
                "total_cost": 0,
                "breakdown": {},
                "note": model_pricing.get("note", "Contact provider for pricing")
            }

        # Calculate costs
        breakdown = {}

        # Input tokens cost
        if use_cache and cache_write_price:
            # With caching, writing to cache costs more
            input_cost = (input_tokens / 1_000_000) * cache_write_price
            breakdown["cache_write"] = {
                "tokens": input_tokens,
                "price_per_million": cache_write_price,
                "cost": input_cost
            }
        else:
            input_cost = (input_tokens / 1_000_000) * input_price
            breakdown["input"] = {
                "tokens": input_tokens,
                "price_per_million": input_price,
                "cost": input_cost
            }

        # Cache read cost
        cache_cost = 0
        if use_cache and cache_read_tokens > 0 and cache_read_price:
            cache_cost = (cache_read_tokens / 1_000_000) * cache_read_price
            breakdown["cache_read"] = {
                "tokens": cache_read_tokens,
                "price_per_million": cache_read_price,
                "cost": cache_cost
            }

        # Output tokens cost
        output_cost = (output_tokens / 1_000_000) * output_price
        breakdown["output"] = {
            "tokens": output_tokens,
            "price_per_million": output_price,
            "cost": output_cost
        }

        total_cost = input_cost + output_cost + cache_cost

        return {
            "total_cost": round(total_cost, 4),
            "total_tokens": input_tokens + output_tokens,
            "deployment": deployment,
            "model": model,
            "breakdown": breakdown
        }

    def calculate_monthly_cost(
        self,
        sessions_per_month: int,
        avg_tokens_per_session: int,
        model: str,
        deployment: str = "direct_api",
        input_ratio: float = 0.3
    ) -> Dict:
        """
        Calculate estimated monthly cost.

        Args:
            sessions_per_month: Number of sessions per month
            avg_tokens_per_session: Average tokens per session
            model: Model ID
            deployment: Deployment method
            input_ratio: Ratio of input to total tokens (default 0.3 = 30% input, 70% output)

        Returns:
            Dict with monthly cost estimate
        """
        total_monthly_tokens = sessions_per_month * avg_tokens_per_session
        input_tokens = int(total_monthly_tokens * input_ratio)
        output_tokens = int(total_monthly_tokens * (1 - input_ratio))

        cost_data = self.calculate_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            deployment=deployment
        )

        if "error" in cost_data:
            return cost_data

        return {
            "monthly_cost": cost_data["total_cost"],
            "sessions_per_month": sessions_per_month,
            "avg_tokens_per_session": avg_tokens_per_session,
            "total_monthly_tokens": total_monthly_tokens,
            "model": model,
            "deployment": deployment,
            "breakdown": cost_data["breakdown"]
        }

    def calculate_savings(
        self,
        current_tokens: int,
        optimized_tokens: int,
        model: str,
        deployment: str = "direct_api",
        input_ratio: float = 0.3
    ) -> Dict:
        """
        Calculate savings from optimization.

        Args:
            current_tokens: Current total tokens
            optimized_tokens: Optimized total tokens
            model: Model ID
            deployment: Deployment method
            input_ratio: Ratio of input tokens

        Returns:
            Dict with savings breakdown
        """
        # Current cost
        current_input = int(current_tokens * input_ratio)
        current_output = int(current_tokens * (1 - input_ratio))
        current_cost_data = self.calculate_cost(
            current_input, current_output, model, deployment
        )

        # Optimized cost
        optimized_input = int(optimized_tokens * input_ratio)
        optimized_output = int(optimized_tokens * (1 - input_ratio))
        optimized_cost_data = self.calculate_cost(
            optimized_input, optimized_output, model, deployment
        )

        if "error" in current_cost_data or "error" in optimized_cost_data:
            return {"error": "Could not calculate savings"}

        savings = current_cost_data["total_cost"] - optimized_cost_data["total_cost"]
        savings_percent = (savings / current_cost_data["total_cost"] * 100) if current_cost_data["total_cost"] > 0 else 0

        return {
            "current_cost": current_cost_data["total_cost"],
            "optimized_cost": optimized_cost_data["total_cost"],
            "savings": round(savings, 4),
            "savings_percent": round(savings_percent, 1),
            "tokens_saved": current_tokens - optimized_tokens,
            "model": model,
            "deployment": deployment
        }

    def get_available_models(self, deployment: str = "direct_api") -> Dict:
        """
        Get list of available models for deployment method.

        Args:
            deployment: Deployment method

        Returns:
            Dict of model IDs and their pricing info
        """
        deployment_config = self.deployment_methods.get(deployment, {})
        return deployment_config.get("models", {})

    def compare_deployments(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> Dict:
        """
        Compare cost across all deployment methods for a model.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model ID

        Returns:
            Dict with costs for each deployment method
        """
        results = {}

        for deployment_name, deployment_config in self.deployment_methods.items():
            if model in deployment_config.get("models", {}):
                cost_data = self.calculate_cost(
                    input_tokens, output_tokens, model, deployment_name
                )
                results[deployment_name] = {
                    "name": deployment_config.get("name"),
                    "cost": cost_data.get("total_cost", 0),
                    "available": "error" not in cost_data
                }

        return results

    def update_user_deployment(
        self,
        deployment: str,
        model: str,
        profile_path: Optional[Path] = None
    ) -> bool:
        """
        Update user's default deployment method and model.

        Args:
            deployment: Deployment method to use
            model: Model to use by default
            profile_path: Path to user_profile.json

        Returns:
            True if successful
        """
        if profile_path is None:
            profile_path = Path.home() / ".claude" / "token-craft" / "user_profile.json"

        try:
            # Load existing profile
            if profile_path.exists():
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
            else:
                profile = {}

            # Update deployment settings
            profile["deployment_method"] = deployment
            profile["default_model"] = model

            # Save
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)

            return True

        except Exception as e:
            print(f"Error updating profile: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    calc = PricingCalculator()

    # Example 1: Calculate cost for a single session
    print("=" * 60)
    print("Example 1: Single Session Cost")
    print("=" * 60)

    cost = calc.calculate_cost(
        input_tokens=4500,
        output_tokens=10500,
        model="claude-sonnet-4-5",
        deployment="direct_api"
    )
    print(f"Direct API (Sonnet 4.5): ${cost['total_cost']:.4f}")

    cost_bedrock = calc.calculate_cost(
        input_tokens=4500,
        output_tokens=10500,
        model="claude-sonnet-4-5",
        deployment="aws_bedrock"
    )
    print(f"AWS Bedrock (Sonnet 4.5): ${cost_bedrock['total_cost']:.4f}")
    print()

    # Example 2: Monthly cost estimate
    print("=" * 60)
    print("Example 2: Monthly Cost Estimate")
    print("=" * 60)

    monthly = calc.calculate_monthly_cost(
        sessions_per_month=80,
        avg_tokens_per_session=15000,
        model="claude-sonnet-4-5",
        deployment="direct_api"
    )
    print(f"Monthly cost (80 sessions @ 15K tokens): ${monthly['monthly_cost']:.2f}")
    print()

    # Example 3: Savings calculation
    print("=" * 60)
    print("Example 3: Optimization Savings")
    print("=" * 60)

    savings = calc.calculate_savings(
        current_tokens=1_200_000,  # 80 sessions × 15K tokens
        optimized_tokens=800_000,   # 80 sessions × 10K tokens (33% improvement)
        model="claude-sonnet-4-5",
        deployment="direct_api"
    )
    print(f"Current cost: ${savings['current_cost']:.2f}/month")
    print(f"Optimized cost: ${savings['optimized_cost']:.2f}/month")
    print(f"Savings: ${savings['savings']:.2f}/month ({savings['savings_percent']}%)")
    print()

    # Example 4: Compare deployments
    print("=" * 60)
    print("Example 4: Deployment Comparison (Sonnet 4.5)")
    print("=" * 60)

    comparison = calc.compare_deployments(
        input_tokens=4500,
        output_tokens=10500,
        model="claude-sonnet-4-5"
    )
    for deployment, data in comparison.items():
        if data["available"]:
            print(f"{data['name']}: ${data['cost']:.4f}")
