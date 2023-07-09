package com.example.demo.repository

import com.example.demo.model.UserTokenEntity
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.stereotype.Repository

@Repository
interface UserTokenRepository: JpaRepository<UserTokenEntity, Long> {
    fun findByToken(token: String): UserTokenEntity?
}