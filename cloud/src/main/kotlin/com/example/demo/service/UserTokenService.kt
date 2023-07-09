package com.example.demo.service

import com.example.demo.model.UserTokenEntity
import com.example.demo.repository.UserTokenRepository
import org.springframework.stereotype.Service
import java.util.UUID.randomUUID

@Service
class UserTokenService (
    val userTokenRepository: UserTokenRepository
) {
    fun getNewToken(): String {
        val userTokenEntity = UserTokenEntity(token = randomUUID().toString())
        return userTokenRepository.save(userTokenEntity).token.orEmpty()
    }

    fun isUserTokenValid(token: String): Boolean {
        val userTokenRecord = userTokenRepository.findByToken(token)
        return userTokenRecord != null
    }
}