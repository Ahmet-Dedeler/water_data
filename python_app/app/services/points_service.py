from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.db.models import (
    UserProfile, PointSource, PointTransaction, PointReward, PointPurchase,
    PointBonus, UserPointBonus, PointTransfer, PointMilestone, UserPointMilestone, User
)
from app.models.points import (
    PointBalance, PointsBreakdown, PointsLeaderboard, PointsStats, PointsEconomy,
    DailyPointsSummary, TransactionType, PointSourceCreate, PointRewardCreate,
    PointBonusCreate, PointMilestoneCreate, PointTransferCreate, PointPurchaseCreate
)

class PointsService:
    def __init__(self):
        self.TRANSFER_FEE_PERCENTAGE = 0.05  # 5% fee on transfers
        self.MIN_TRANSFER_AMOUNT = 10
        self.MAX_TRANSFER_AMOUNT = 10000

    def get_user_balance(self, db: Session, user_id: int) -> Optional[PointBalance]:
        """Get comprehensive point balance for a user"""
        user_profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not user_profile:
            return None

        # Calculate lifetime earned and spent
        lifetime_earned = db.query(func.sum(PointTransaction.points_amount)).filter(
            PointTransaction.user_id == user_id,
            PointTransaction.transaction_type.in_(['earned', 'bonus'])
        ).scalar() or 0

        lifetime_spent = db.query(func.sum(PointTransaction.points_amount)).filter(
            PointTransaction.user_id == user_id,
            PointTransaction.transaction_type.in_(['spent', 'transfer'])
        ).scalar() or 0

        # Get last transaction date
        last_transaction = db.query(PointTransaction).filter(
            PointTransaction.user_id == user_id
        ).order_by(desc(PointTransaction.created_at)).first()

        return PointBalance(
            user_id=user_id,
            total_points=user_profile.points,
            lifetime_earned=lifetime_earned,
            lifetime_spent=lifetime_spent,
            available_points=user_profile.points,
            last_transaction_date=last_transaction.created_at if last_transaction else None
        )

    def add_points(self, db: Session, user_id: int, points_to_add: int, source_name: str = "general", description: str = None, reference_type: str = None, reference_id: int = None) -> Dict[str, Any]:
        """Add points to a user with full transaction tracking"""
        user_profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not user_profile:
            return {"success": False, "message": "User profile not found"}

        # Get or create point source
        point_source = db.query(PointSource).filter_by(name=source_name).first()
        if not point_source:
            point_source = PointSource(
                name=source_name,
                base_points=points_to_add,
                description=f"Auto-created for {source_name}"
            )
            db.add(point_source)
            db.commit()
            db.refresh(point_source)

        # Check daily/weekly limits
        if not self._check_source_limits(db, user_id, point_source.id, points_to_add):
            return {"success": False, "message": "Daily or weekly limit exceeded for this source"}

        # Apply multipliers
        final_points = int(points_to_add * point_source.multiplier)

        # Apply active bonuses
        bonus_multiplier = self._get_active_bonus_multiplier(db, user_id)
        final_points = int(final_points * bonus_multiplier)

        # Update user balance
        old_balance = user_profile.points
        user_profile.points += final_points
        new_balance = user_profile.points

        # Create transaction record
        transaction = PointTransaction(
            user_id=user_id,
            point_source_id=point_source.id,
            transaction_type=TransactionType.EARNED,
            points_amount=final_points,
            balance_after=new_balance,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id
        )
        db.add(transaction)

        # Check for milestone achievements
        milestones_achieved = self._check_point_milestones(db, user_id, new_balance)

        db.add(user_profile)
        db.commit()

        return {
            "success": True,
            "points_added": final_points,
            "old_balance": old_balance,
            "new_balance": new_balance,
            "source_multiplier": point_source.multiplier,
            "bonus_multiplier": bonus_multiplier,
            "milestones_achieved": milestones_achieved
        }

    def subtract_points(self, db: Session, user_id: int, points_to_subtract: int, description: str = None, reference_type: str = None, reference_id: int = None) -> Dict[str, Any]:
        """Subtract points from a user"""
        user_profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not user_profile:
            return {"success": False, "message": "User profile not found"}

        if user_profile.points < points_to_subtract:
            return {"success": False, "message": "Insufficient points"}

        old_balance = user_profile.points
        user_profile.points -= points_to_subtract
        new_balance = user_profile.points

        # Create transaction record
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=TransactionType.SPENT,
            points_amount=points_to_subtract,
            balance_after=new_balance,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id
        )
        db.add(transaction)
        db.add(user_profile)
        db.commit()

        return {
            "success": True,
            "points_subtracted": points_to_subtract,
            "old_balance": old_balance,
            "new_balance": new_balance
        }

    def transfer_points(self, db: Session, sender_id: int, transfer_data: PointTransferCreate) -> Dict[str, Any]:
        """Transfer points between users"""
        # Validate transfer amount
        if transfer_data.points_amount < self.MIN_TRANSFER_AMOUNT:
            return {"success": False, "message": f"Minimum transfer amount is {self.MIN_TRANSFER_AMOUNT}"}
        
        if transfer_data.points_amount > self.MAX_TRANSFER_AMOUNT:
            return {"success": False, "message": f"Maximum transfer amount is {self.MAX_TRANSFER_AMOUNT}"}

        # Check sender balance
        sender_profile = db.query(UserProfile).filter_by(user_id=sender_id).first()
        if not sender_profile:
            return {"success": False, "message": "Sender profile not found"}

        # Calculate transfer fee
        transfer_fee = int(transfer_data.points_amount * self.TRANSFER_FEE_PERCENTAGE)
        total_cost = transfer_data.points_amount + transfer_fee

        if sender_profile.points < total_cost:
            return {"success": False, "message": "Insufficient points including transfer fee"}

        # Check receiver exists
        receiver_profile = db.query(UserProfile).filter_by(user_id=transfer_data.receiver_id).first()
        if not receiver_profile:
            return {"success": False, "message": "Receiver profile not found"}

        # Perform transfer
        sender_profile.points -= total_cost
        receiver_profile.points += transfer_data.points_amount

        # Create transfer record
        transfer = PointTransfer(
            sender_id=sender_id,
            receiver_id=transfer_data.receiver_id,
            points_amount=transfer_data.points_amount,
            message=transfer_data.message,
            transfer_fee=transfer_fee
        )
        db.add(transfer)

        # Create transaction records
        sender_transaction = PointTransaction(
            user_id=sender_id,
            transaction_type=TransactionType.TRANSFER,
            points_amount=total_cost,
            balance_after=sender_profile.points,
            description=f"Transfer to user {transfer_data.receiver_id}",
            reference_type="transfer",
            reference_id=transfer.id
        )
        
        receiver_transaction = PointTransaction(
            user_id=transfer_data.receiver_id,
            transaction_type=TransactionType.EARNED,
            points_amount=transfer_data.points_amount,
            balance_after=receiver_profile.points,
            description=f"Transfer from user {sender_id}",
            reference_type="transfer",
            reference_id=transfer.id
        )

        db.add_all([sender_transaction, receiver_transaction, sender_profile, receiver_profile])
        db.commit()

        return {
            "success": True,
            "points_transferred": transfer_data.points_amount,
            "transfer_fee": transfer_fee,
            "sender_new_balance": sender_profile.points,
            "receiver_new_balance": receiver_profile.points
        }

    def purchase_reward(self, db: Session, user_id: int, purchase_data: PointPurchaseCreate) -> Dict[str, Any]:
        """Purchase a reward with points"""
        # Get reward
        reward = db.query(PointReward).filter_by(id=purchase_data.point_reward_id).first()
        if not reward or not reward.is_available:
            return {"success": False, "message": "Reward not available"}

        # Check user level requirement
        user_profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not user_profile:
            return {"success": False, "message": "User profile not found"}

        if user_profile.level < reward.required_level:
            return {"success": False, "message": f"Level {reward.required_level} required"}

        # Check purchase limits
        if reward.purchase_limit_per_user:
            user_purchases = db.query(PointPurchase).filter(
                PointPurchase.user_id == user_id,
                PointPurchase.point_reward_id == reward.id
            ).count()
            
            if user_purchases + purchase_data.quantity > reward.purchase_limit_per_user:
                return {"success": False, "message": "Purchase limit exceeded"}

        # Check stock
        if reward.is_limited and reward.stock_quantity is not None:
            if reward.stock_quantity < purchase_data.quantity:
                return {"success": False, "message": "Insufficient stock"}

        # Calculate total cost
        total_cost = reward.cost_points * purchase_data.quantity

        # Check user balance
        if user_profile.points < total_cost:
            return {"success": False, "message": "Insufficient points"}

        # Process purchase
        user_profile.points -= total_cost

        # Update stock
        if reward.is_limited and reward.stock_quantity is not None:
            reward.stock_quantity -= purchase_data.quantity

        # Create purchase record
        purchase = PointPurchase(
            user_id=user_id,
            point_reward_id=reward.id,
            points_spent=total_cost,
            quantity=purchase_data.quantity
        )
        db.add(purchase)

        # Create transaction record
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=TransactionType.SPENT,
            points_amount=total_cost,
            balance_after=user_profile.points,
            description=f"Purchased {reward.name} x{purchase_data.quantity}",
            reference_type="purchase",
            reference_id=purchase.id
        )
        db.add(transaction)

        db.add_all([user_profile, reward])
        db.commit()

        return {
            "success": True,
            "reward_name": reward.name,
            "quantity": purchase_data.quantity,
            "points_spent": total_cost,
            "new_balance": user_profile.points
        }

    def get_points_breakdown(self, db: Session, user_id: int, days: int = 30) -> Optional[PointsBreakdown]:
        """Get detailed points breakdown for a user"""
        user_profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not user_profile:
            return None

        # Get points by source
        points_by_source_query = db.query(
            PointSource.name,
            func.sum(PointTransaction.points_amount).label('total_points')
        ).join(
            PointTransaction, PointSource.id == PointTransaction.point_source_id
        ).filter(
            PointTransaction.user_id == user_id,
            PointTransaction.transaction_type == TransactionType.EARNED
        ).group_by(PointSource.name).all()

        points_by_source = {source.name: source.total_points for source in points_by_source_query}

        # Get recent transactions
        recent_transactions = db.query(PointTransaction).filter(
            PointTransaction.user_id == user_id
        ).order_by(desc(PointTransaction.created_at)).limit(20).all()

        # Get daily points for last N days
        start_date = datetime.utcnow() - timedelta(days=days)
        daily_points_query = db.query(
            func.date(PointTransaction.created_at).label('date'),
            func.sum(func.case([(PointTransaction.transaction_type.in_(['earned', 'bonus']), PointTransaction.points_amount)], else_=0)).label('earned'),
            func.sum(func.case([(PointTransaction.transaction_type.in_(['spent', 'transfer']), PointTransaction.points_amount)], else_=0)).label('spent')
        ).filter(
            PointTransaction.user_id == user_id,
            PointTransaction.created_at >= start_date
        ).group_by(func.date(PointTransaction.created_at)).all()

        daily_points_last_30_days = [
            {"date": str(day.date), "earned": day.earned, "spent": day.spent, "net": day.earned - day.spent}
            for day in daily_points_query
        ]

        # Get top earning sources
        top_earning_sources = [
            {"source": source.name, "total_points": source.total_points}
            for source in sorted(points_by_source_query, key=lambda x: x.total_points, reverse=True)[:5]
        ]

        # Get spending categories
        spending_query = db.query(
            PointReward.category,
            func.sum(PointPurchase.points_spent).label('total_spent')
        ).join(
            PointPurchase, PointReward.id == PointPurchase.point_reward_id
        ).filter(
            PointPurchase.user_id == user_id
        ).group_by(PointReward.category).all()

        spending_categories = {cat.category or 'Other': cat.total_spent for cat in spending_query}

        return PointsBreakdown(
            user_id=user_id,
            current_balance=user_profile.points,
            points_by_source=points_by_source,
            recent_transactions=recent_transactions,
            daily_points_last_30_days=daily_points_last_30_days,
            top_earning_sources=top_earning_sources,
            spending_categories=spending_categories
        )

    def get_points_leaderboard(self, db: Session, leaderboard_type: str = "total", limit: int = 20) -> PointsLeaderboard:
        """Get points leaderboard"""
        if leaderboard_type == "total":
            query = db.query(
                User.id,
                User.username,
                UserProfile.points
            ).join(
                UserProfile, User.id == UserProfile.user_id
            ).order_by(desc(UserProfile.points)).limit(limit)
        elif leaderboard_type == "earned":
            query = db.query(
                User.id,
                User.username,
                func.sum(PointTransaction.points_amount).label('total_earned')
            ).join(
                UserProfile, User.id == UserProfile.user_id
            ).join(
                PointTransaction, User.id == PointTransaction.user_id
            ).filter(
                PointTransaction.transaction_type.in_(['earned', 'bonus'])
            ).group_by(User.id, User.username).order_by(
                desc('total_earned')
            ).limit(limit)
        elif leaderboard_type == "spent":
            query = db.query(
                User.id,
                User.username,
                func.sum(PointTransaction.points_amount).label('total_spent')
            ).join(
                UserProfile, User.id == UserProfile.user_id
            ).join(
                PointTransaction, User.id == PointTransaction.user_id
            ).filter(
                PointTransaction.transaction_type.in_(['spent', 'transfer'])
            ).group_by(User.id, User.username).order_by(
                desc('total_spent')
            ).limit(limit)
        else:
            raise ValueError("Invalid leaderboard type")

        results = query.all()
        entries = []
        
        for i, result in enumerate(results):
            entry = {
                "rank": i + 1,
                "user_id": result.id,
                "username": result.username
            }
            
            if leaderboard_type == "total":
                entry["points"] = result.points
            elif leaderboard_type == "earned":
                entry["total_earned"] = result.total_earned or 0
            elif leaderboard_type == "spent":
                entry["total_spent"] = result.total_spent or 0
            
            entries.append(entry)

        total_users = db.query(UserProfile).count()

        return PointsLeaderboard(
            entries=entries,
            total_users=total_users,
            leaderboard_type=leaderboard_type
        )

    def get_points_stats(self, db: Session) -> PointsStats:
        """Get overall points statistics"""
        total_users = db.query(UserProfile).count()
        total_points_in_circulation = db.query(func.sum(UserProfile.points)).scalar() or 0
        
        total_points_earned = db.query(func.sum(PointTransaction.points_amount)).filter(
            PointTransaction.transaction_type.in_(['earned', 'bonus'])
        ).scalar() or 0
        
        total_points_spent = db.query(func.sum(PointTransaction.points_amount)).filter(
            PointTransaction.transaction_type.in_(['spent', 'transfer'])
        ).scalar() or 0

        average_user_balance = total_points_in_circulation / total_users if total_users > 0 else 0
        active_point_sources = db.query(PointSource).filter_by(is_active=True).count()
        available_rewards = db.query(PointReward).filter_by(is_available=True).count()
        total_transactions = db.query(PointTransaction).count()

        # Most popular reward
        popular_reward = db.query(
            PointReward.name,
            func.count(PointPurchase.id).label('purchase_count')
        ).join(
            PointPurchase, PointReward.id == PointPurchase.point_reward_id
        ).group_by(PointReward.name).order_by(
            desc('purchase_count')
        ).first()

        most_popular_reward = popular_reward.name if popular_reward else None

        return PointsStats(
            total_users=total_users,
            total_points_in_circulation=total_points_in_circulation,
            total_points_earned=total_points_earned,
            total_points_spent=total_points_spent,
            average_user_balance=average_user_balance,
            active_point_sources=active_point_sources,
            available_rewards=available_rewards,
            total_transactions=total_transactions,
            most_popular_reward=most_popular_reward
        )

    def _check_source_limits(self, db: Session, user_id: int, source_id: int, points_amount: int) -> bool:
        """Check if adding points would exceed daily/weekly limits"""
        source = db.query(PointSource).filter_by(id=source_id).first()
        if not source:
            return True

        # Check daily limit
        if source.daily_limit:
            today = datetime.utcnow().date()
            daily_total = db.query(func.sum(PointTransaction.points_amount)).filter(
                PointTransaction.user_id == user_id,
                PointTransaction.point_source_id == source_id,
                func.date(PointTransaction.created_at) == today,
                PointTransaction.transaction_type == TransactionType.EARNED
            ).scalar() or 0
            
            if daily_total + points_amount > source.daily_limit:
                return False

        # Check weekly limit
        if source.weekly_limit:
            week_start = datetime.utcnow().date() - timedelta(days=datetime.utcnow().weekday())
            weekly_total = db.query(func.sum(PointTransaction.points_amount)).filter(
                PointTransaction.user_id == user_id,
                PointTransaction.point_source_id == source_id,
                func.date(PointTransaction.created_at) >= week_start,
                PointTransaction.transaction_type == TransactionType.EARNED
            ).scalar() or 0
            
            if weekly_total + points_amount > source.weekly_limit:
                return False

        return True

    def _get_active_bonus_multiplier(self, db: Session, user_id: int) -> float:
        """Get active bonus multiplier for a user"""
        now = datetime.utcnow()
        bonuses = db.query(PointBonus).filter(
            PointBonus.is_active == True,
            PointBonus.start_date <= now,
            PointBonus.end_date >= now
        ).all()

        total_multiplier = 1.0
        for bonus in bonuses:
            # Check if user meets requirements (simplified)
            total_multiplier *= bonus.multiplier

        return total_multiplier

    def _check_point_milestones(self, db: Session, user_id: int, new_balance: int) -> List[Dict[str, Any]]:
        """Check and award point milestones"""
        # Get milestones that user hasn't achieved yet
        achieved_milestones = db.query(UserPointMilestone.point_milestone_id).filter_by(user_id=user_id).subquery()
        
        new_milestones = db.query(PointMilestone).filter(
            PointMilestone.points_threshold <= new_balance,
            PointMilestone.is_active == True,
            ~PointMilestone.id.in_(achieved_milestones)
        ).all()

        milestones_achieved = []
        for milestone in new_milestones:
            # Award milestone
            user_milestone = UserPointMilestone(
                user_id=user_id,
                point_milestone_id=milestone.id
            )
            db.add(user_milestone)
            
            milestones_achieved.append({
                "title": milestone.title,
                "description": milestone.description,
                "threshold": milestone.points_threshold,
                "reward_type": milestone.reward_type,
                "reward_value": milestone.reward_value,
                "badge": milestone.badge_emoji
            })

        return milestones_achieved

    # Admin methods for managing point sources and rewards
    def create_point_source(self, db: Session, source_data: PointSourceCreate) -> PointSource:
        """Create a new point source"""
        source = PointSource(**source_data.model_dump())
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    def create_point_reward(self, db: Session, reward_data: PointRewardCreate) -> PointReward:
        """Create a new point reward"""
        reward = PointReward(**reward_data.model_dump())
        db.add(reward)
        db.commit()
        db.refresh(reward)
        return reward

    def create_point_milestone(self, db: Session, milestone_data: PointMilestoneCreate) -> PointMilestone:
        """Create a new point milestone"""
        milestone = PointMilestone(**milestone_data.model_dump())
        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        return milestone

points_service = PointsService() 